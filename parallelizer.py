import csv
import argparse
from tqdm import tqdm
from ast import literal_eval
import gzip
from pathlib import Path
from typing import List, Tuple, Set
import torchaudio
import torch
import os
import re


def segment_audio(waveform: torch.Tensor, sr: int, timestamps: List[Tuple[float, float]]) -> torch.Tensor:
    """Extract and concatenate segments from audio based on timestamp intervals."""
    duration = waveform.size(1)
    segments = [
        waveform[:, int(start * sr):min(int(end * sr), duration)]
        for start, end in timestamps
    ]
    return torch.cat(segments, dim=1) if segments else None


def segment_target(manifest: Path, root: Path, out_root: Path) -> None:
    """Segments Greek audio using the timestamp info from the Spanish manifest."""
    out_root.mkdir(parents=True, exist_ok=True)
    open_func = gzip.open if str(manifest).endswith(".gz") else open

    with open_func(manifest, "rt", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="|")

        success, total, skipped = 0, 0, 0

        for row in tqdm(reader, desc="Segmenting Greek Audio"):
            total += 1
            session_id = row["session_id"]
            segment_id = row["id_"].replace(":", "-")
            timestamps = literal_eval(row["vad"])

            if not session_id.startswith("2009"):
                continue

            greek_file = root / f"{session_id}_el.ogg"
            if not greek_file.exists():
                skipped += 1
                continue

            try:
                waveform, sr = torchaudio.load(greek_file)
                segment = segment_audio(waveform, sr, timestamps)
                print("audio segmented")
                #validate segment
                if segment is None or segment.size(1) < sr:  # less than 1 second
                    skipped += 1
                    continue

                if not torch.isfinite(segment).all() or torch.all(segment == 0):
                    skipped += 1
                    continue


                out_name = f"{session_id}-el_{segment_id}.wav" # make sure output is in .wav format
                out_path = out_root / out_name

                import subprocess

                # save in .wav format
                subprocess.run(["ffmpeg", "-y", "-i", str(greek_file), str(out_path)])
                
                # segment
                torchaudio.save(str(out_path), segment, sr)
                success += 1

            except Exception as e:
                print(f"Error with {session_id}_{segment_id}: {e}")
                skipped += 1

    print(f"\n✅ Segmentation complete: {success}/{total} segments created.")
    print(f"❌ Skipped: {skipped} segments.\n")


def intersect(dir1: Path, dir2: Path) -> Tuple[Set[str], Set[str], Set[str]]:
    """Return common filenames and unpaired files between two directories."""

    def get_time_segment(filename: str) -> str:
        # '...el_es_20091217-15-09-34_5.wav' -> '20091217-15-09-34_5.wav'
        match = re.search(r'(\d{8}-\d{2}-\d{2}-\d{2}_\d+\.wav)$', filename)
        if match:
            return match.group(0)
        else:
            return filename  # fallback (won't match)

    files1 = list(dir1.glob("*.wav"))
    files2 = list(dir2.glob("*.wav"))    

    key_to_file1 = {get_time_segment(f.name): f.name for f in files1}
    key_to_file2 = {get_time_segment(f.name): f.name for f in files2}

    keys1 = set(key_to_file1)
    keys2 = set(key_to_file2)
    
    common_keys = keys1 & keys2
    only1_keys = keys1 - keys2
    only2_keys = keys2 - keys1

    common = {key_to_file1[k] for k in common_keys}
    only1 = {key_to_file1[k] for k in only1_keys}
    only2 = {key_to_file2[k] for k in only2_keys}

    return common, only1, only2


def get_parallel_ids(langs : list[str], target_dir: Path, source_dir: Path, common_files: Set[str], out_path: Path) -> None:
    """Generate a TSV manifest of parallel Greek–Spanish audio files."""
    with open(out_path, "w", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        
        # correspondence between lang[0] and lang[1]
        writer.writerow(langs)
        for fname in sorted(common_files):
            target_path = target_dir / fname
            spanish_path = source_dir / fname
            writer.writerow([str(target_path), str(spanish_path)])

def main(langs: str, manifest_path: Path, source_root : Path[str], target_root: Path, target_out_root: Path):
    """Main orchestration function for segmenting and aligning Greek–Spanish audio."""
    
    # segment target {el} audio using {es} manifest of segments and timestamps
    lang_codes = langs.strip().split()
    segment_target(manifest_path, target_root, target_out_root)

    common, _, _ = intersect(target_out_root, source_root)

    # correspondence between {el} and {es} parallel audios
    manifest_out = target_out_root / f"parallel_{lang_codes[0]}-{lang_codes[1]}.tsv"
    get_parallel_ids(lang_codes, target_out_root, source_root, common, manifest_out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--langs", type=str, required=True,
                        help="Space-separated language pair (e.g. 'el es') — target first, then source")
    parser.add_argument("--source-manifest", type=Path, required=True,
                        help="Path to Spanish TSV or TSV.GZ with VAD info (e.g. asr_es.tsv.gz)")
    parser.add_argument("--source-root", type=Path, required=True,
                        help="Path to segmented Spanish audio files (WAV files)")
    parser.add_argument("--target-root", type=Path, required=True,
                        help="Path to raw Greek audio directory (OGG files)")
    parser.add_argument("--output-root", type=Path, required=True,
                        help="Output path for segmented Greek audio files (WAV files)")
    args = parser.parse_args()

    main(args.langs, args.source_manifest, args.source_root, args.target_root, args.output_root)
