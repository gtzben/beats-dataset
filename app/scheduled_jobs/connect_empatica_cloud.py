"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-12-09
"""
import pandas as pd
import os, re, io, boto3

from avro.io import DatumReader
from avro.datafile import DataFileReader


BUCKET_NAME = "empatica-us-east-1-prod-data"
LOCATION= "v2/1559/"
RAW_DIR = "data/raw"
LOGGER = None


def convert_acc_units(acc):
    """
    Converts accelerometer ADC counts to physical units (g).
    """
    delta_physical = acc["imuParams"]["physicalMax"] - acc["imuParams"]["physicalMin"]
    delta_digital = acc["imuParams"]["digitalMax"] - acc["imuParams"]["digitalMin"]
    return {
        "x": [val * delta_physical / delta_digital for val in acc["x"]],
        "y": [val * delta_physical / delta_digital for val in acc["y"]],
        "z": [val * delta_physical / delta_digital for val in acc["z"]]
    }


def process_signal(data, signal_name, columns, filekey):
    """
    Processes a signal and writes it to a CSV file.
    
    Parameters:
        data (dict): The raw signal data.
        signal_name (str): Name of the signal (used for file naming).
        output_dir (str): Directory to save the CSV file.
        columns (list): Column names for the CSV.
        unit_conversion (callable, optional): A function to apply unit conversion to the data.
    """


    signal = data["rawData"].get(signal_name)
    if not signal:
        LOGGER.warning("Signal not in AVRO file")
        return
    
    sampling_freq = signal.get("samplingFrequency", 0)  # Get frequency, default to 0
        
    if (sampling_freq == 0) and signal_name in ["accelerometer", "eda", "temperature", "bvp"]:
        LOGGER.warning(f"Faulty {signal_name} signal for filekey {filekey} : Sampling frequency is 0")
        df_signal = pd.DataFrame(columns=columns)
        df_signal.name = signal_name
        return df_signal  # return empty DataFrame

    if "unix_timestamp" in columns:

        values = "x" if "x" in columns else "values"

        # Calculate timestamps
        timestamp = [
            round(signal["timestampStart"] + i * (1e6 / sampling_freq))
            for i in range(len(signal[values]))
        ]
        
        # Convert units if a conversion function is provided
        if signal_name == "accelerometer":
            processed_data = convert_acc_units(signal)
            rows = [[ts] + [processed_data[col][i] for col in columns[1:]] for i, ts in enumerate(timestamp)]
        else:
            rows = [[ts, sig] for ts, sig in zip(timestamp, signal[values])]

    else:

        rows = [[sig] for sig in signal[columns[0]]]
    
    df_signal = pd.DataFrame(rows, columns=columns)
    df_signal.name=signal_name

    return df_signal


# Main function to process the AVRO file
def process_avro_file_from_s3(file_key, s3_client):

    # Download the Avro file content into memory
    response = s3_client.get_object(Bucket=BUCKET_NAME, Key=file_key)
    avro_data = response['Body'].read()

    # Use a BytesIO stream to read the Avro file from memory
    avro_stream = io.BytesIO(avro_data)
    reader = DataFileReader(avro_stream, DatumReader())
    data = next(reader)

    # Process signals - Keep the order in mind
    df_signals = [process_signal(data, "accelerometer", ["unix_timestamp", "x", "y", "z"], file_key),
    process_signal(data, "gyroscope", ["unix_timestamp", "x", "y", "z"], file_key),
    process_signal(data, "eda", ["unix_timestamp", "eda"], file_key),
    process_signal(data, "temperature", ["unix_timestamp", "temperature"], file_key),
    process_signal(data, "bvp", ["unix_timestamp", "bvp"], file_key),
    process_signal(data, "steps", ["unix_timestamp", "steps"], file_key),
    process_signal(data, "tags", ["tagsTimeMicros"], file_key),
    process_signal(data, "systolicPeaks", ["peaksTimeNanos"], file_key)]

    return df_signals


def get_files_from_s3_ts_range(participant_id, serial_number, date, started_at, ended_at,
                       last_session_ts, logger, offset_minutes=30):
    """
    
    """

    global LOGGER
    LOGGER = logger

    offset_seconds = offset_minutes*60

    skipped=False

    s3 = boto3.client('s3')
    
    # Prefix based on the known directory structure
    prefix = os.path.join(LOCATION, f"1/1/participant_data/{date}/{participant_id}-{serial_number}/raw_data/v6/")

    # Create a regex pattern to match timestamps within the range
    file_pattern = re.compile(
        fr"1-1-{participant_id}_(?P<timestamp>\d+)\.avro$"
    )
    
    response = s3.list_objects_v2(
        Bucket=BUCKET_NAME,
        Prefix=prefix
    )
    
    # Collecting files that match the specific participant_id and timestamp pattern
    signals_session = []
    avro_timestamps = []
    if 'Contents' in response:

        for obj in response['Contents']:
            file_key = obj['Key']

            match = file_pattern.search(file_key)
            
            if match:
                # Extract the timestamp from the filename
                file_timestamp = int(match.group("timestamp"))

                # Check if the timestamp falls within the range
                if started_at - offset_seconds <= file_timestamp <= ended_at + offset_seconds:

                    if file_timestamp <= last_session_ts:
                        skipped=True
                        continue

                    df_signals = process_avro_file_from_s3(file_key, s3)
                    signals_session.append(df_signals)

                    avro_timestamps.append(file_timestamp)

    list_df_signals = [pd.concat(list(signals), ignore_index=True) for signals in zip(*signals_session)]
    
    return list_df_signals, avro_timestamps, skipped