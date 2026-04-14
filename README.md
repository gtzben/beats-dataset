
<div align="center" style="font-size: 1.8em;">
  <strong>Unlock the Therapeutic Potential of Music: The BEATS Dataset</strong>
  <br><br>
</div>

<div align="center"> 
<a href="https://beats-dataset.github.io/">
  <img src="https://img.shields.io/badge/Website Webpage-4F6D8A?style=for-the-badge">
</a>
<a href="https://dl.acm.org/doi/10.1145/3714394.3756341">
  <img src="https://img.shields.io/badge/Paper-ACM-EA5E58?style=for-the-badge">
</a>
<a href="#">
  <img src="https://img.shields.io/badge/Dataset-%F0%9F%A4%97%20HuggingFace-F6B26B?style=for-the-badge">
</a>
</div>

<br>

<div align="center">
<a href="https://gtzben.github.io/" target="_blank">Benjamin&nbsp;Gutierrez&nbsp;Serafin</a> &emsp;
<a href="https://www.tanayag.com/" target="_blank">Tanaya&nbsp;Guha</a> &emsp;
<a href="https://www.fahim-kawsar.net/" target="_blank">Fahim&nbsp;Kawsar</a>
</div>

---

# Introduction 
The **BEATS Dataset**—*Biomarkers, Experience and Affect from Therapeutic Soundscapes*—is a music dataset with aligned physiological data collected in-the-wild. It is designed to support research at the intersection of music therapy, affective computing, well-being, and signal processing, among others.

All data is anonymised, and each participant record includes:
- Demographic information (e.g., gender, age)
- Individual differences (e.g., personality traits, music preferences)
- Wellbeing measures (e.g., pre/post stress, depression levels)
- Music listening activity and playback context (aligned with physiology, ~275 hours)
- Raw physiological signals (BVP and EDA, indexing affective states) (>10,000 hours)
- Self-reported evaluations of the therapeutic effect of playlists

This repository contains the system infrastructure for collecting, storing, and managing the BEATS dataset, including integration with the EmbracePlus wearable device and Spotify API.

---

## 🛠 Data Collection System Setup

### 1. Install Required Software

Ensure the following software is installed:

- Python 3.8. Newer versions may work but are not tested. Using [pyenv](https://github.com/pyenv/pyenv?tab=readme-ov-file#a-getting-pyenv) or other python version manager is recommended.
- [sqlite3](https://www.geeksforgeeks.org/how-to-install-sqlite-3-in-ubuntu/)
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

### 2. Configure AWS CLI

Set up your Access Key and Secret Key to enable automatic download of physiological data from Empatica Cloud.  
Refer to [Empatica's guide](https://support.empatica.com/hc/en-us/articles/13879014347421-Accessing-Data-on-the-S3-Bucket) for configuration details.

### 3. Clone the Repository

```bash
git clone https://github.com/gtzben/beats-dataset.git && cd beats-dataset
```

### 4. Create a Local Environment
```bash
python -m venv env
source env/bin/activate
```

### 5. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 6. Configure Environment
Fill out the template files and remove the `.template` extensions:
```bash
cp config.ini.template config.ini
cp stimuli.yaml.template stimuli.yaml
```
Edit them to match your environment, stimuli and API credentials.

### 7. Initialise the Database
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
flask reset-db
```
This creates the database schema and seeds default data (e.g., questionnaires).

### 8. Mount Cloud Storage (Optional)
Use [rclone](https://rclone.org) to mount cloud storage to the data/raw directory, e.g., OneDrive or Google Drive.
```bash
rclone mount remote:dataset ./data/raw
--allow-other \
--allow-non-empty \
--vfs-cache-mode writes \
--log-file .data/logs/rclone-onedrive.log \
--log-level INFO
```


### 9. Run the Service

- Option A: Flask Terminal `python run.py` or, run Flask as a service using [systemd](https://blog.miguelgrinberg.com/post/running-a-flask-application-as-a-service-with-systemd) (Development)
- Option B: [uWSGI + Reverse Proxy ](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-uwsgi-and-nginx-on-ubuntu-22-04) (Production).

### 10. Setup Scheduled Jobs

Use cron to run the scheduled Flask jobs defined in `app/scheduled_jobs`.
See this [guide](https://blog.miguelgrinberg.com/post/run-your-flask-regularly-scheduled-jobs-with-cron) for setup details.

---

## 📄 License
Please refer to `LICENSE.md` for licensing details.


## 📚 Citation

If you use the BEATS dataset or collection system, please cite:

```bash

@inproceedings{gutierrez2025towards,
  title={Towards Capturing the Therapeutic Effects of Music in Everyday Life: Building the Beats Dataset},
  author={Gutierrez Serafin, Benjamin and Guha, Tanaya and Kawsar, Fahim},
  booktitle={Companion of the 2025 ACM International Joint Conference on Pervasive and Ubiquitous Computing},
  pages={1665--1669},
  year={2025}
}

```