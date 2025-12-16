# End-to-End IoT System with Raspberry Pi Emulation, AWS IoT, and Real-Time Dashboard

## 📋 Overview

This project implements a complete, secure IoT pipeline that simulates a Raspberry Pi device, transmits data to AWS IoT Core via MQTT with TLS encryption, stores it in DynamoDB, and visualizes it through a real-time web dashboard. The system demonstrates core IoT architecture principles with integrated security at every layer.

**Architecture Flow:** 
Raspberry Pi (QEMU) → MQTT/TLS → AWS IoT Core → IoT Rule → DynamoDB ↔ Flask API → Web Dashboard

## 🎯 Quick Start

```bash
# Clone the repository
git clone <https://github.com/RYANFRANKLIN237/Raspberry-pi-AWS-Web.git>
cd iot-web-dashboard

# Install Python dependencies
pip install -r requirements.txt

# Configure environment variables
# Edit .env with your AWS credentials

# Run the dashboard
python app.py

# Access at http://localhost:5000
```

#### **1. `.env` File (Create this - NOT in repository for security)**
```bash
# AWS Academy/Learner Lab Credentials
AWS_REGION=us-east-1
DYNAMODB_TABLE=IoTDeviceData
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_SESSION_TOKEN=your_session_token_here  # For temporary credentials

# MQTT Configuration
MQTT_ENDPOINT=xxxxxxxxxxxx-ats.iot.us-east-1.amazonaws.com
MQTT_TOPIC=rpi/data
```




---

## 🖥️ Part 1: Setting Up Raspberry Pi Emulation with QEMU

### **For macOS/Linux Users**

#### **Step 1: Install QEMU**
```bash
# macOS (using Homebrew)
brew install qemu

# Linux (Ubuntu/Debian)
sudo apt-get install qemu-system-arm qemu-utils
```

#### **Step 2: Create Working Directory**
```bash
mkdir ~/qemu_rpi
cd ~/qemu_rpi
```

#### **Step 3: Download Required Files**
```bash
# Download compatible Raspberry Pi OS (Jessie Lite - Required!)
curl -O https://downloads.raspberrypi.org/raspbian_lite/images/raspbian_lite-2017-04-10/2017-04-10-raspbian-jessie-lite.zip
unzip 2017-04-10-raspbian-jessie-lite.zip
mv 2017-04-10-raspbian-jessie-lite.img raspbian-jessie.img

# Download QEMU-compatible kernel
git clone https://github.com/dhruvvyas90/qemu-rpi-kernel.git
cp qemu-rpi-kernel/kernel-qemu-4.4.34-jessie .
cp qemu-rpi-kernel/versatile-pb.dtb .
```

#### **Step 4: Boot the Emulator**
```bash
qemu-system-arm \
  -kernel kernel-qemu-4.4.34-jessie \
  -cpu arm1176 \
  -m 256 \
  -M versatilepb \
  -append "root=/dev/sda2 panic=1 rootfstype=ext4 rw" \
  -hda raspbian-jessie.img \
  -serial stdio \
  -no-reboot
```

**⚠️ Important Notes:**
- Use only **Jessie or Stretch** images - newer versions won't boot
- Default login: `pi` / `raspberry`
- Network is enabled via QEMU user networking (host accessible at `10.0.2.2`)

### **For Windows Users**

#### **Step 1: Install QEMU**
1. Download QEMU for Windows from [qemu.org](https://www.qemu.org/download/#windows)
2. Install and add to PATH during installation
3. Open PowerShell or Command Prompt as Administrator

#### **Step 2: Setup Directory**
```powershell
mkdir C:\qemu_rpi
cd C:\qemu_rpi
```

#### **Step 3: Download Files**
```powershell
# Download using PowerShell
Invoke-WebRequest -Uri "https://downloads.raspberrypi.org/raspbian_lite/images/raspbian_lite-2017-04-10/2017-04-10-raspbian-jessie-lite.zip" -OutFile "raspbian-jessie.zip"
Expand-Archive -Path raspbian-jessie.zip -DestinationPath .

# Download kernel (use git or direct download)
git clone https://github.com/dhruvvyas90/qemu-rpi-kernel.git
copy qemu-rpi-kernel\kernel-qemu-4.4.34-jessie .
copy qemu-rpi-kernel\versatile-pb.dtb .
```

#### **Step 4: Boot Command (PowerShell)**
```powershell
& "C:\Program Files\qemu\qemu-system-arm.exe" `
  -kernel kernel-qemu-4.4.34-jessie `
  -cpu arm1176 `
  -m 256 `
  -M versatilepb `
  -dtb versatile-pb.dtb `
  -append "root=/dev/sda2 rootfstype=ext4 rw console=ttyAMA0" `
  -drive file=raspbian-jessie.img,format=raw `
  -serial stdio `
  -no-reboot
```

---

## 📁 Part 2: Transferring Files to QEMU Emulator

### **Method A: HTTP Server (Recommended)**

#### **On Host Machine:**
```bash
# Create directory and copy files
mkdir -p ~/qemu_shared
cp -R /path/to/AWS_IOT_DEVICE ~/qemu_shared/

# Create tarball
cd ~/qemu_shared
tar -czf aws_iot_device.tar.gz AWS_IOT_DEVICE

# Start HTTP server (keep this terminal open)
python3 -m http.server 8000
# For Python 2: python -m SimpleHTTPServer 8000
```

#### **Inside QEMU Raspberry Pi:**
```bash
# Install wget if needed
sudo apt-get update
sudo apt-get install wget -y

# Download files
mkdir -p ~/aws_transfer
cd ~/aws_transfer
wget http://10.0.2.2:8000/aws_iot_device.tar.gz

# Extract
tar -xzf aws_iot_device.tar.gz
cp -R AWS_IOT_DEVICE ~/
```

### **Method B: Using SCP (Alternative)**
If you enabled SSH in QEMU (port forwarding):

```bash
# From host to QEMU
scp -P 2222 -r /path/to/AWS_IOT_DEVICE pi@localhost:~/
```

---

## ⚙️ Part 3: Configuring Raspberry Pi Environment

### **Install Required Packages in QEMU**
```bash
# Update package list
sudo apt-get update

# Install Python and dependencies
sudo apt-get install python python-pip python-setuptools -y

# Install MQTT client
sudo pip install paho-mqtt

# Install additional utilities
sudo apt-get install wget curl nano -y
```

### **Prepare Python Environment**
```bash
# Navigate to your IoT directory
cd ~/AWS_IOT_DEVICE

# Install required packages
sudo pip install -r requirements.txt
# Or install individually:
# sudo pip install paho-mqtt
```

---

## ☁️ Part 4: AWS IoT Core Configuration

### **Step 1: Create IoT Thing**
1. Go to **AWS IoT Console** → **All devices** → **Things**
2. Click **Create thing**
3. Choose **Create single thing**
4. Name: `RaspberryPiEmulator1`
5. Click **Next** (skip additional configuration)

### **Step 2: Generate Certificates**
1. Under **Security**, choose **Create certificate**
2. Download all files:
   - **Device certificate** (`certificate.pem.crt`)
   - **Private key** (`private.pem.key`)
   - **Amazon Root CA** (`AmazonRootCA1.pem`)
3. **Activate** the certificate
4. **Attach policy** (create one if needed)

### **Step 3: Create IoT Policy**
1. Go to **Secure** → **Policies** → **Create policy**
2. Policy name: `RaspberryPiPolicy`
3. Policy JSON:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iot:Connect",
      "Resource": "arn:aws:iot:*:*:client/RaspberryPiEmulator1"
    },
    {
      "Effect": "Allow",
      "Action": "iot:Publish",
      "Resource": "arn:aws:iot:*:*:topic/rpi/data"
    }
  ]
}
```
4. Attach this policy to your certificate

### **Step 4: Note Your Endpoint**
1. Go to **Settings** in AWS IoT Console
2. Copy your **Device data endpoint** (looks like: `xxxxxxxxxxxx-ats.iot.region.amazonaws.com`)

---

## 🐍 Part 5: Raspberry Pi Python Application

### **File Structure in QEMU**
```
/home/pi/AWS_IOT_DEVICE/
├── iot_publish.py          # Main IoT publisher
├── AmazonRootCA1.pem       # AWS Root CA
├── certificate.pem.crt     # Device certificate
└── private.pem.key         # Private key
```

### **Configure the Publisher**
Edit `iot_publish.py` with your endpoint:

```python
AWS_ENDPOINT = "xxxxxxxxxxxx-ats.iot.us-east-1.amazonaws.com"  # Your endpoint
CLIENT_ID = "RaspberryPiEmulator1"
TOPIC = "rpi/data"

# Certificate paths (relative to script location)
CA = "./AmazonRootCA1.pem"
CERT = "./certificate.pem.crt"
KEY = "./private.pem.key"
```

### **Run the IoT Publisher**
```bash
cd ~/AWS_IOT_DEVICE
python iot_publish.py
```

**Expected Output:**
```
Connected with result code 0
Publishing: {"device_id": "RaspberryPiEmulator1", "value": 42, ...}
```

---

## 💾 Part 6: DynamoDB Data Storage

### **Create DynamoDB Table**
1. Go to **DynamoDB Console** → **Create table**
2. Table name: `IoTDeviceData`
3. Partition key: `device_id` (String)
4. Sort key: `timestamp` (Number)
5. Click **Create**

### **Create IoT Rule for DynamoDB**
1. Go to **AWS IoT Console** → **Message routing** → **Rules**
2. Click **Create rule**
3. Name: `StoreInDynamoDB`
4. SQL statement: `SELECT * FROM 'rpi/data'`
5. **Add action**: **Split message into multiple columns of a DynamoDB table**
6. Configure:
   - Table name: `IoTDeviceData`
   - Partition key: `device_id`
   - Partition key value: `${device_id}`
   - Sort key: `timestamp`
   - Sort key value: `${timestamp}`
7. Create/select IAM role with DynamoDB write permissions

---

## 🌐 Part 7: Web Dashboard Setup

### **Run Flask App**
```bash
cd iot-web-dashboard
```

### **Install Python Dependencies**
```bash
pip install -r requirements.txt
# Or install manually:
pip install Flask Flask-CORS boto3 paho-mqtt python-dotenv
```

### **Configuration Files**

#### **1. `.env` File (Create this - NOT in repository for security)**
```bash
# AWS Academy/Learner Lab Credentials
AWS_REGION=us-east-1
DYNAMODB_TABLE=IoTDeviceData
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_SESSION_TOKEN=your_session_token_here  # For temporary credentials

# MQTT Configuration
MQTT_ENDPOINT=xxxxxxxxxxxx-ats.iot.us-east-1.amazonaws.com
MQTT_TOPIC=rpi/data
```

#### **2. Certificate Files**
Place these in the project root (same as `app.py`):
- `AmazonRootCA1.pem`
- `certificate.pem.crt` 
- `private.pem.key`

**⚠️ Security Note:** These files contain sensitive credentials. **NEVER commit them to Git**. They are excluded via `.gitignore`.

### **Project Structure**
```
iot-web-dashboard/
├── app.py                    # Flask application
├── config.py                 # Configuration loader
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create this)
├── AmazonRootCA1.pem         # AWS certificates (add these)
├── certificate.pem.crt       #
├── private.pem.key           #
├── static/
│   ├── css/
│   │   └── style.css        # Dashboard styles
│   └── js/
│       └── app.js           # Frontend logic
├── templates/
│   └── index.html           # Dashboard HTML
└── .gitignore               # Excludes sensitive files
```

### **Run the Dashboard**
```bash
python app.py
```

Access at: **http://localhost:5000**

### **Dashboard Features**
- **Live Data Tab**: Real-time MQTT stream from Raspberry Pi
- **Historical Data Tab**: Query DynamoDB with interactive chart
- **Auto-refresh**: Live updates every 5 seconds

---

## 🔧 Troubleshooting

### **Common QEMU Issues**

| Problem | Solution |
|---------|----------|
| **"Warning: Neither atags nor dtb found"** | Use `-dtb versatile-pb.dtb` in boot command |
| **Kernel panic / Can't mount root** | Use correct root device: `root=/dev/sda2` or `root=/dev/mmcblk0p2` |
| **Network not working** | Host is at `10.0.2.2` in QEMU user networking |
| **Keyboard issues (@ instead of ")** | Change layout: `sudo raspi-config` → Localisation → Keyboard |

### **AWS IoT Connection Issues**

| Error | Solution |
|-------|----------|
| **"UnrecognizedClientException"** | Add `AWS_SESSION_TOKEN` for temporary credentials |
| **Certificate errors** | Ensure all 3 certificate files exist in correct paths |
| **MQTT connection timeout** | Verify endpoint and region match |
| **Policy denied** | Attach policy with `iot:Connect` and `iot:Publish` permissions |

### **Dashboard Issues**

| Error | Solution |
|-------|----------|
| **"No such file or directory" (certs)** | Place certificate files in project root |
| **DynamoDB Decimal conversion error** | Updated code handles Decimal to float conversion |
| **MQTT not streaming** | Check Flask logs for connection errors |
| **"Module object has no attribute PROTOCOL_TLS"** | Use `ssl.PROTOCOL_TLSv1_2` for older Python |

---

## 📊 Testing the Complete System

1. **Start Raspberry Pi emulator** and run `iot_publish.py`
2. **Verify AWS IoT Console** → Test → MQTT test client (subscribe to `rpi/data`)
3. **Check DynamoDB** for stored items
4. **Start dashboard** with `python app.py`
5. **Open browser** to `http://localhost:5000`

All tabs should show data updating in real-time.

---

## 🔒 Security Considerations

**⚠️ Important Security Practices:**

1. **Never commit sensitive files to Git**:
   - Certificate files (`.pem`, `.crt`, `.key`)
   - `.env` file with credentials
   - AWS access keys

2. **Use IAM roles with least privilege**:
   - Device: Only `connect` and `publish` to specific topic
   - Dashboard: Only read from DynamoDB
   - IoT Rule: Only write to specific DynamoDB table

3. **Rotate credentials regularly** (especially AWS Academy tokens)

4. **Use TLS 1.2 for all MQTT connections**

---

## 🚀 Advanced Customization

### **Custom Data Format**
Modify `iot_publish.py` to send different data:

```python
payload = {
    "device_id": CLIENT_ID,
    "timestamp": int(time.time()),
    "sensor_type": "temperature",
    "value": random.randint(20, 30),
    "unit": "celsius",
    "location": "lab_room_1"
}
```

### **Modify Dashboard**
- Edit `static/js/app.js` for frontend logic
- Modify `static/css/style.css` for styling
- Update `templates/index.html` for layout changes

### **Scale the System**
- Add multiple simulated devices with different client IDs
- Implement device shadow for desired/actual state
- Add S3 storage for long-term data archival
- Implement user authentication for dashboard

---

## 📚 Resources & References

- **QEMU Documentation**: https://www.qemu.org/docs/
- **AWS IoT Developer Guide**: https://docs.aws.amazon.com/iot
- **Paho MQTT Python Client**: https://github.com/eclipse/paho.mqtt.python
- **Flask Documentation**: https://flask.palletsprojects.com/
- **DynamoDB Documentation**: https://docs.aws.amazon.com/dynamodb
- **Register raspberry pi to aws iot core tutorial**: https://youtu.be/adKuyckikuw?si=Ddf2e80Z2UFVK4KD
- **Store data sent to iot core in dynamodb using lambda tutorial**: https://youtu.be/0RcVwTKSbSA?si=a1a_86_CInxmr5GP

- **More Apps by Me**: https://play.google.com/store/apps/details?id=com.savanna.instaknow

---

## ⚠️ Disclaimer

This project is for educational purposes.Learner Lab credentials expire frequently. For production use:
- Use permanent IAM users/roles
- Implement proper error handling
- Add monitoring and alerting
- Follow AWS Well-Architected Framework
- Implement proper logging

---

## 🎉 Success Criteria

Your system is working when:
- ✅ Raspberry Pi emulator boots successfully
- ✅ Python script connects to AWS IoT Core
- ✅ Data appears in AWS IoT MQTT Test Client
- ✅ Items are stored in DynamoDB table
- ✅ Dashboard runs without errors
- ✅ All three tabs show live/ historical/statistical data
- ✅ Data updates in real-time as Raspberry Pi publishes

**Need help?** Check the troubleshooting section or create an issue in the repository.
