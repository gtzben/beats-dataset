# The BEATS Dataset 🎵 - System for Data Collection

The **BEATS Dataset**—*Biomarkers, Experience and Affect from Therapeutic Soundscapes*—is a music dataset with aligned physiological data collected in-the-wild. It is designed to support research at the intersection of music therapy, affective computing, well-being, and signal processing, among others.

All data is anonymised, and each participant record includes:
- Demographic information (e.g., gender, age)
- Individual differences (e.g., personality traits, music preferences)
- Wellbeing measures (e.g., pre/post stress, depression levels)
- Music listening activity and playback context
- Raw physiological signals (BVP and EDA, indexing affective states)
- Self-reported evaluations of the therapeutic effect of playlists

This repository contains the system infrastructure for collecting, storing, and managing the BEATS dataset, including integration with the EmbracePlus wearable device and Spotify API.

---

## 🛠 Setup Instructions

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

## 📄 License & Citation
Please refer to `LICENSE.md` for licensing details.
If you use The BEATS Dataset or the collection system in your work, please cite the associated publication (to be added upon release).