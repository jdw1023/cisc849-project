# CISC849 Final Project

## Setup

1. **Clone the repository to your local machine:**

   ```bash
   git clone https://github.com/jdw1023/cisc849-project.git
   cd cisc849-project
   ```
2. **Create a virtual environment (optional but recommended):**
  ```bash
  python -m venv venv
  ```
3. **Activate the virtual environment:**
  
  ```bash
  source venv/bin/activate
  ```
  
4. **Install the project dependencies:**
  ```bash
  pip install -r requirements.txt
  ```

5. **Run the program:**
  ```bash
  python3 captioning_gui3.py
  ```

The software is tested on a Laptop running Ubuntu 22.04 LTS with Python 3.10.6. The default configuration for (Whisper_Streaming)[https://github.com/ufal/whisper_streaming] is to run on GPU using NVIDIA CUDA. So a system with CUDA support is needed.