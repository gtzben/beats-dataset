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

<br>

<img alt="beats-protocol" src="https://github.com/user-attachments/assets/38b20866-718a-445e-9489-c63df5b654f1" />

---

# Introduction 
The **BEATS Dataset** (Biomarkers, Experience and Affect from Therapeutic Soundscapes) is a longitudinal collection of raw physiological
signals from music listeners in free-moving environments, enabling
the study of music–physiology relationships in real-world settings.

Data were collected using the Empatica EmbracePlus device, capturing multimodal physiological signals alongside self-paced listening to curated therapeutic playlists, self-reports of perceived effects, individual differences, and
pre/post-experiment well-being measure.

It includes data from **30 participants** monitored over **21 days**, yielding **10,725 hours** of raw physiological recordings from PPG, EDA, skin temperature, and triaxial accelerometry. Notably, a subset of **262.2 hours** is aligned
with music playback, corresponding to **844 listening sessions** across
**3 music listening contexts** involving **117 curated tracks**.

BEATS is uniquely positioned to support research in:
- music therapy and digital health
- affective computing and multimodal modelling
- personalised intervention and recommendation systems

<br>

<img alt="physio-music-align" src="https://github.com/user-attachments/assets/e47ef5b9-3c93-4e58-94ad-eda72ca96e12" />

<br>

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
