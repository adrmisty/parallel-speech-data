# Spanish &harr; Greek Speech dataset

> * **Author:** Adriana Rodríguez Flórez (adrirflorez@gmail.com)
> * **Course:** NPFL087 Machine Translation, Summer 2024/2025
> * **Faculty:** ÚFAL at Matfyz in Charles University (Prague)
> * **Supervisors:** Doc Rndr. Ondřej Bojar and Mgr. Dominik Macháček
> * **Dates:** March - May 2025

## 📄 Project Overview

This project presents a pipeline to construct a **Spanish-Greek parallel speech corpus**. Speech translation research has historically focused on high-resource, English-centric pipelines, leaving many language pairs like Spanish-Greek underrepresented. Greek, in particular, lacks robust annotated speech corpora and ASR tools.

This gap often forces researchers to rely on pivot-based translation (e.g., Greek &rarr; English &rarr; Spanish), which can introduce errors and lose significant nuance in meaning, formality, and prosody[cite: 18, 26, 27].

This work serves as a **proof of concept** for building direct speech-to-speech (S2S) resources for low-resource language pairs, demonstrating a feasible, if computationally intensive, pipeline.

## 💾 Data Source

The corpus is built using recordings from the **Vox Populi dataset** , which contains recordings of European Parliament plenary sessions.

- **Source:** 2009 subset of Vox Populi.
- **Challenge:** While the Spanish audio in Vox Populi is well-supported with transcriptions and metadata, the Greek audio is only available as raw, unannotated interpretation audio[cite: 20, 58, 87].
- **Solution:** This project's pipeline uses the Spanish metadata to process and align the raw Greek audio.

## ⚙️ Methodology & Pipeline

The project follows a three-stage pipeline:

1. **Audio Segmentation:** The raw Greek audio files are segmented using the Voice Activity Detection (VAD) timestamps from the parallel Spanish ASR manifest[cite: 107, 114, 115]. This is the primary function of the `parallelizer.py` script.
2.  **Transcription:** Both the Spanish and segmented Greek audio files are transcribed using WhisperX / Faster Whisper**. A `large-v3` model was used for Spanish, and a custom fine-tuned `large-v2-greek` model was used for Greek to improve accuracy.
3.  **Sentence Alignment:** The resulting text transcripts are aligned at the sentence level using **HunAlign**[cite: 108, 112, 155].

## 🚀 Usage: `parallelizer.py`

This repository includes the `parallelizer.py` script, which performs **Step 1** of the pipeline. It segments the raw target (Greek) audio files using the source (Spanish) manifest and then creates a new manifest of the matched parallel audio files.

### Dependencies

You will need the following to run the script:

* Python 3.8+
* PyTorch (`torch`)
* Torchaudio (`torchaudio`)
* tqdm
* **FFmpeg**: This must be installed on your system and available in your PATH, as it is used via `subprocess` for audio conversion.


You can install the Python dependencies using `pip`:

```bash
pip install torch torchaudio tqdm
```

### Running the Script
The script is run from the command line and accepts several arguments to define the input and output paths.

```Bash
python parallelizer.py \
    --langs "el es" \
    --source-manifest /path/to/spanish/asr_es.tsv.gz \
    --source-root /path/to/segmented_spanish_wavs/ \
    --target-root /path/to/raw_greek_oggs/ \
    --output-root /path/to/output_segmented_greek/


#### Arguments
--langs: Space-separated language pair, with the target language (Greek) first and the source language (Spanish) second (e.g., 'el es').

--source-manifest: Path to the source Spanish TSV or TSV.GZ file that contains the VAD timestamp information (e.g., asr_es.tsv.gz).

--source-root: Path to the directory containing the already-segmented Spanish .wav audio files.

--target-root: Path to the directory containing the raw, full-length Greek .ogg audio files.

--output-root: The directory where the script will save the newly segmented Greek .wav files.
```

#### Output
The script will:

1. Create segmented Greek .wav files in the specified --output-root directory.

2. Generate a parallel_el-es.tsv file in the --output-root listing the file paths for each matched Greek and Spanish audio segment, ready for the transcription step.



---



## 📊 Results and Limitations

### Results

The pipeline was proven feasible. From an initial pool of 2470 matched segment pairs from the 2009 data , a sample of 33 high-quality segment pairs was successfully processed and aligned.

### Limitations

The primary bottleneck is the lack of computational resources. Transcription and alignment are very time- and resource-intensive. Furthermore, Greek ASR performance, while improved with a custom model, remains a significant challenge.

---

## 🔮 Future Work
To build upon this proof of concept, future efforts could include:


- Scaling the dataset: Process the full 2009-2020 Vox Populi dataset to transcribe and align all 2470+ identified pairs.

- Upgrading alignment: Move from HunAlign to more robust neural alignment systems like SeamlessAlign or SONAR-based embeddings.

- Releasing the corpus: Publish the final, cleaned parallel corpus on a platform like HuggingFace or LINDAT to benefit the research community.

---

🙏 Acknowledgments
This project was supervised by Doc Rndr. Ondřej Bojar and Mgr. Dominik Macháček as part of the NPFL087 Statistical Machine Translation course at ÚFAL, Charles University, Prague.