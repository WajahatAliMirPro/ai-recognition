# 🎓 AI-Powered Attendance System

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green.svg)](https://opencv.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Ready-brightgreen.svg)](https://www.mongodb.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An intelligent, feature-rich desktop application that revolutionizes attendance tracking using facial recognition technology. Built with Python, Tkinter, and OpenCV, with seamless MongoDB cloud integration.

## 📖 Project Overview
This project aims to provide an efficient and accurate attendance tracking system using advanced facial recognition technology. The application is designed to simplify the process of marking attendance, making it faster and more reliable.

## 🤖 Algorithm
The core algorithm utilizes a deep learning model for facial recognition, which is trained on a dataset of student images. The model processes live video feed from a webcam to detect and recognize faces in real-time, ensuring accurate attendance marking.

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🎨 **Modern UI** | Clean, dark-themed, user-friendly interface |
| 📸 **Smart Registration** | Quick student enrollment via webcam capture |
| 🤖 **AI Training** | One-click facial recognition model training |
| ⚡ **Real-time Detection** | Instant student recognition and attendance marking |
| ⏱️ **Timed Sessions** | Configurable duration for attendance periods |
| ☁️ **Cloud Sync** | Automatic MongoDB database synchronization |
| 🔄 **Offline Support** | Local storage with later sync capability |
| 📊 **Analytics** | Comprehensive attendance history viewing |
| 📥 **Export Options** | Filter and export records by subject/date |

## 🚀 Setup and Installation
### Prerequisites
- Python 3.7+
- A webcam connected to your computer.

### 1. Download Required Model Files
This project uses a pre-trained deep neural network (DNN) model for accurate face detection. You need to download two files:
- deploy.prototxt.txt
- res10_300x300_ssd_iter_140000.caffemodel

You can often find these as part of OpenCV's official repository or other public sources. Place both of these files in the same root directory as the Python scripts.

### 2. Install Dependencies
A requirements.txt file is provided to install all necessary Python packages. Open your terminal or command prompt and run:

```bash
pip install -r requirements.txt
```

### 3. Run the Application
After setting up the environment, you can run the application using:

```bash
python main.py
```

### 4. Syncing Data
The offline_sync_log.txt file is then updated with only the paths of files that still failed to sync, ready for the next attempt.

## 📄 License
This project is licensed under the MIT License. See the LICENSE file for more details.

---

For more information, please refer to the documentation or contact the project maintainers.