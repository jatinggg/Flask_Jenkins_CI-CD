# Jenkins CI/CD Pipeline for Flask Student Management Application

A complete CI/CD pipeline setup for a Flask-based student management application using Jenkins, GitHub webhooks, and automated testing.

## Installation

### VM Setup

Update your VM and install required dependencies:

```bash
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install -y python3 python3-pip python3-venv

# Install MongoDB
sudo apt install -y mongodb

# Start and enable MongoDB
sudo systemctl start mongodb
sudo systemctl enable mongodb

# Verify MongoDB
sudo systemctl status mongodb
```

### Jenkins Setup

#### Install Java

```bash
sudo apt install -y openjdk-11-jdk

# Verify installation
java -version
```

#### Install Jenkins

```bash
# Add Jenkins repository
wget -q -O - https://pkg.jenkins.io/debian/jenkins.io.key | sudo apt-key add -
sudo sh -c 'echo deb http://pkg.jenkins.io/debian-stable binary/ > /etc/apt/sources.list.d/jenkins.list'

# Install and start Jenkins
sudo apt update
sudo apt install -y jenkins

sudo systemctl start jenkins
sudo systemctl enable jenkins

# Check status
sudo systemctl status jenkins
```

#### Access Jenkins

1. Navigate to `http://your-vm-ip:8080`
2. Retrieve the initial admin password:
   ```bash
   sudo cat /var/lib/jenkins/secrets/initialAdminPassword
   ```
   
3. Complete the setup wizard and install recommended plugins
     


### Repository Setup

Clone the repository into your VM:

```bash
git clone https://github.com/jatinggg/Flask_Jenkins_CI-CD.git
cd Jenkins_flask_Practice
```


**Now go inside the cloned repo and create our Jenkinsfile, test file and update our requirement.txt**
- `Jenkinsfile` - Pipeline configuration
- `requirements.txt` - Python dependencies
- `test_*.py` - Unit test files

## Configuration

### GitHub Webhooks

Set up automatic build triggers when code is pushed:

1. Go to your GitHub repository
2. Click **Settings** → **Webhooks** → **Add webhook**
3. Configure as follows:
   - **Payload URL:** `http://your-vm-ip:8080/github-webhook/`
   - **Content type:** `application/json`
   - **Which events:** Select "Just the push event"
   - **Active:** Check the box
4. Click **Add webhook**

### Email Notifications

#### Configure SMTP for Extended Email Notifications

1. Go to **Manage Jenkins** → **Configure System**
2. Scroll to **Extended E-mail Notification**
3. Set the following:
   - **SMTP server:** `smtp.gmail.com`
   - **SMTP Port:** `465`
   - Check **Use SSL**
   - Add Jenkins credentials
4. Click **Save**

#### Configure Default Email Settings

1. In **Configure System**, scroll to **E-mail Notification**
2. Set the following:
   - **SMTP server:** `smtp.gmail.com`
   - **User Name:** Your Gmail address
   - **Password:** Your Google app password (not regular password)
   - **SMTP Port:** `465`
   - Check **Use SMTP Authentication**
   - Check **Use SSL**
   - **Reply-To Address:** Your Gmail address
   
3. Click **Test configuration** to send a test email
4. Click **Save**
   You will recieve the test mail on your Gmail account

### Jenkins Credentials

#### Add MongoDB URI Credential

1. Go to **Manage Jenkins** → **Manage Credentials**
2. Click **(global)** domain
3. Click **Add Credentials**
4. Configure as follows:
   - **Kind:** Secret text
   - **Scope:** Global
   - **Secret:** `mongodb+srv://username:password@cluster.mongodb.net/student_db?retryWrites=true&w=majority`
   - **ID:** `MONGO_URI`
   - **Description:** MongoDB Connection String
5. Click **OK**
 
#### Add Flask Secret Key Credential

1. Repeat the above steps with:
   - **Kind:** Secret text
   - **Scope:** Global
   - **Secret:** Your random secret key
   - **ID:** `SECRET_KEY`
   - **Description:** Flask Secret Key
2. Click **OK**
 

### Pipeline Setup

1. Go to Jenkins Dashboard
2. Click **New Item**
3. Enter name: `Flask-Student-App-Pipeline`
4. Select **Pipeline**
5. Click **OK**

#### Configure General Settings

- **Description:** CI/CD Pipeline for Flask Student Management Application
- Check **GitHub project**
- **Project URL:** `https://github.com/jatinggg/Flask_Jenkins_CI-CD.git`
 
#### Configure Build Triggers

- Check **GitHub hook trigger for GITScm polling**

#### Configure Pipeline

- **Definition:** Pipeline script from SCM
- **SCM:** Git
- **Repository URL:** `https://github.com/jatinggg/Flask_Jenkins_CI-CD.git`
- **Credentials:** Leave as none if public repo
- **Branch Specifier:** `*/main`
- **Script Path:** `Jenkinsfile`

Click **Save**

## Usage

The pipeline is automatically triggered when you push changes to the main branch:

```bash
git add .
git commit -m "Your commit message"
git push origin main
```

**Our build is triggered and pipeline is working successfully**


Jenkins will:
1. Detect the webhook trigger
2. Clone the latest code
3. Run unit tests
4. Build the application
6. Send email notifications on success or failure
   Check your Gmail Account

8. Deploy the application

## Application Access

Once the pipeline completes successfully, access your Flask application at:

```
http://your-vm-ip:8000/
```

