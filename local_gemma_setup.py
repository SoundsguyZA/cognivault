#!/usr/bin/env python3
"""
Local Gemma Setup for CogniVault
Install and configure Ollama with Gemma models
VERITAS BUILD - Local AI without Corporate Dependencies
"""

import subprocess
import requests
import json
import platform
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

class LocalGemmaSetup:
    def __init__(self):
        """Initialize Gemma setup"""
        self.system = platform.system().lower()
        self.architecture = platform.machine().lower()
        
        self.ollama_config = {
            'download_urls': {
                'windows': 'https://ollama.ai/download/windows',
                'macos': 'https://ollama.ai/download/darwin',
                'linux': 'https://ollama.ai/download/linux'
            },
            'api_port': 11434,
            'models': {
                'gemma2:2b': {
                    'size': '1.6GB',
                    'description': 'Gemma 2B - Fast and efficient for local use',
                    'recommended': True
                },
                'gemma2:9b': {
                    'size': '5.4GB', 
                    'description': 'Gemma 9B - Higher quality, requires more resources',
                    'recommended': False
                },
                'gemma:7b': {
                    'size': '4.8GB',
                    'description': 'Original Gemma 7B model',
                    'recommended': False
                }
            }
        }
    
    def check_ollama_installation(self) -> Dict[str, Any]:
        """Check if Ollama is installed and running"""
        try:
            # Check if ollama command is available
            result = subprocess.run(['ollama', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                version = result.stdout.strip()
                
                # Check if service is running
                api_status = self.check_ollama_api()
                
                return {
                    'installed': True,
                    'version': version,
                    'api_running': api_status['running'],
                    'api_status': api_status
                }
            else:
                return {'installed': False, 'error': 'Ollama not found'}
        
        except FileNotFoundError:
            return {'installed': False, 'error': 'Ollama not in PATH'}
        except subprocess.TimeoutExpired:
            return {'installed': False, 'error': 'Ollama command timeout'}
        except Exception as e:
            return {'installed': False, 'error': str(e)}
    
    def check_ollama_api(self) -> Dict[str, Any]:
        """Check if Ollama API is running"""
        try:
            response = requests.get(f'http://localhost:{self.ollama_config["api_port"]}/api/tags', timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                
                return {
                    'running': True,
                    'models': [model['name'] for model in models],
                    'model_count': len(models)
                }
            else:
                return {'running': False, 'error': f'API returned {response.status_code}'}
        
        except requests.ConnectionError:
            return {'running': False, 'error': 'Connection refused - Ollama not running'}
        except requests.Timeout:
            return {'running': False, 'error': 'API timeout'}
        except Exception as e:
            return {'running': False, 'error': str(e)}
    
    def install_ollama(self) -> Dict[str, Any]:
        """Install Ollama based on the operating system"""
        if self.system == 'windows':
            return self.install_ollama_windows()
        elif self.system == 'darwin':  # macOS
            return self.install_ollama_macos()
        elif self.system == 'linux':
            return self.install_ollama_linux()
        else:
            return {'success': False, 'error': f'Unsupported OS: {self.system}'}
    
    def install_ollama_windows(self) -> Dict[str, Any]:
        """Install Ollama on Windows"""
        return {
            'success': False,
            'error': 'Windows installation requires manual download',
            'instructions': [
                '1. Download Ollama from: https://ollama.ai/download/windows',
                '2. Run the installer as administrator',
                '3. Restart your command prompt',
                '4. Run: ollama --version to verify installation'
            ]
        }
    
    def install_ollama_macos(self) -> Dict[str, Any]:
        """Install Ollama on macOS"""
        try:
            # Try Homebrew first
            result = subprocess.run(['brew', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                print("Installing Ollama via Homebrew...")
                install_result = subprocess.run(['brew', 'install', 'ollama'], 
                                              capture_output=True, text=True, timeout=300)
                
                if install_result.returncode == 0:
                    return {'success': True, 'method': 'homebrew'}
                else:
                    return {
                        'success': False, 
                        'error': f'Homebrew install failed: {install_result.stderr}'
                    }
            else:
                return {
                    'success': False,
                    'error': 'Homebrew not found',
                    'instructions': [
                        '1. Install Homebrew: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"',
                        '2. Then run: brew install ollama',
                        'OR download manually from: https://ollama.ai/download/darwin'
                    ]
                }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def install_ollama_linux(self) -> Dict[str, Any]:
        """Install Ollama on Linux"""
        try:
            print("Installing Ollama on Linux...")
            
            # Download and install Ollama
            install_command = 'curl -fsSL https://ollama.ai/install.sh | sh'
            
            result = subprocess.run(install_command, shell=True, 
                                  capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return {'success': True, 'method': 'curl_install'}
            else:
                return {
                    'success': False,
                    'error': f'Installation failed: {result.stderr}',
                    'stdout': result.stdout
                }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def start_ollama_service(self) -> Dict[str, Any]:
        """Start Ollama service"""
        try:
            if self.system == 'windows':
                # On Windows, Ollama should start automatically after installation
                return self.check_ollama_api()
            
            else:
                # On Unix systems, start ollama serve
                print("Starting Ollama service...")
                
                # Start in background
                process = subprocess.Popen(['ollama', 'serve'], 
                                         stdout=subprocess.PIPE, 
                                         stderr=subprocess.PIPE)
                
                # Wait a moment for startup
                time.sleep(3)
                
                # Check if it's running
                api_status = self.check_ollama_api()
                
                if api_status['running']:
                    return {'success': True, 'pid': process.pid, 'api_status': api_status}
                else:
                    return {'success': False, 'error': 'Service started but API not responding'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def install_gemma_model(self, model_name: str = 'gemma2:2b') -> Dict[str, Any]:
        """Install specific Gemma model"""
        if model_name not in self.ollama_config['models']:
            return {'success': False, 'error': f'Unknown model: {model_name}'}
        
        model_info = self.ollama_config['models'][model_name]
        
        try:
            print(f"Installing {model_name} ({model_info['size']})...")
            print("This may take several minutes depending on your internet connection.")
            
            result = subprocess.run(['ollama', 'pull', model_name], 
                                  capture_output=True, text=True, timeout=1800)  # 30 min timeout
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'model': model_name,
                    'size': model_info['size'],
                    'output': result.stdout
                }
            else:
                return {
                    'success': False,
                    'error': f'Model installation failed: {result.stderr}',
                    'stdout': result.stdout
                }
        
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Model download timeout (30 minutes)'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_gemma_model(self, model_name: str = 'gemma2:2b') -> Dict[str, Any]:
        """Test Gemma model with a simple query"""
        try:
            payload = {
                'model': model_name,
                'prompt': 'Hello! Please respond with a brief greeting.',
                'stream': False
            }
            
            response = requests.post(
                f'http://localhost:{self.ollama_config["api_port"]}/api/generate',
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'model': model_name,
                    'response': result.get('response', ''),
                    'response_length': len(result.get('response', '')),
                    'load_duration': result.get('load_duration', 0),
                    'prompt_eval_duration': result.get('prompt_eval_duration', 0)
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_installed_models(self) -> Dict[str, Any]:
        """Get list of installed models"""
        try:
            response = requests.get(f'http://localhost:{self.ollama_config["api_port"]}/api/tags', timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                
                gemma_models = []
                other_models = []
                
                for model in models:
                    if 'gemma' in model['name'].lower():
                        gemma_models.append(model)
                    else:
                        other_models.append(model)
                
                return {
                    'success': True,
                    'total_models': len(models),
                    'gemma_models': gemma_models,
                    'other_models': other_models
                }
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def complete_setup(self, model_name: str = 'gemma2:2b') -> Dict[str, Any]:
        """Complete setup process"""
        setup_steps = []
        
        # Step 1: Check installation
        print("Step 1: Checking Ollama installation...")
        install_check = self.check_ollama_installation()
        setup_steps.append({'step': 'installation_check', 'result': install_check})
        
        if not install_check['installed']:
            print("Step 2: Installing Ollama...")
            install_result = self.install_ollama()
            setup_steps.append({'step': 'installation', 'result': install_result})
            
            if not install_result['success']:
                return {
                    'success': False,
                    'error': 'Installation failed',
                    'steps': setup_steps
                }
        
        # Step 3: Start service
        print("Step 3: Starting Ollama service...")
        service_result = self.start_ollama_service()
        setup_steps.append({'step': 'service_start', 'result': service_result})
        
        if not service_result['success']:
            return {
                'success': False,
                'error': 'Service start failed',
                'steps': setup_steps
            }
        
        # Step 4: Install model
        print(f"Step 4: Installing {model_name} model...")
        model_result = self.install_gemma_model(model_name)
        setup_steps.append({'step': 'model_install', 'result': model_result})
        
        if not model_result['success']:
            return {
                'success': False,
                'error': 'Model installation failed',
                'steps': setup_steps
            }
        
        # Step 5: Test model
        print("Step 5: Testing model...")
        test_result = self.test_gemma_model(model_name)
        setup_steps.append({'step': 'model_test', 'result': test_result})
        
        return {
            'success': test_result['success'],
            'model': model_name,
            'steps': setup_steps,
            'final_test': test_result
        }
    
    def get_setup_instructions(self) -> Dict[str, Any]:
        """Get platform-specific setup instructions"""
        instructions = {
            'system': self.system,
            'architecture': self.architecture,
            'recommended_model': 'gemma2:2b',
            'steps': []
        }
        
        if self.system == 'windows':
            instructions['steps'] = [
                '1. Download Ollama from https://ollama.ai/download/windows',
                '2. Run the installer as administrator',
                '3. Open Command Prompt and run: ollama pull gemma2:2b',
                '4. Test with: ollama run gemma2:2b "Hello"'
            ]
        
        elif self.system == 'darwin':
            instructions['steps'] = [
                '1. Install Homebrew if not installed',
                '2. Run: brew install ollama',
                '3. Start service: ollama serve',
                '4. In new terminal: ollama pull gemma2:2b',
                '5. Test with: ollama run gemma2:2b "Hello"'
            ]
        
        elif self.system == 'linux':
            instructions['steps'] = [
                '1. Run: curl -fsSL https://ollama.ai/install.sh | sh',
                '2. Start service: ollama serve',
                '3. In new terminal: ollama pull gemma2:2b',
                '4. Test with: ollama run gemma2:2b "Hello"'
            ]
        
        return instructions
    
    def create_status_report(self) -> Dict[str, Any]:
        """Create comprehensive status report"""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'system_info': {
                'os': self.system,
                'arch': self.architecture
            }
        }
        
        # Check installation
        install_status = self.check_ollama_installation()
        report['installation'] = install_status
        
        if install_status['installed']:
            # Check API
            api_status = self.check_ollama_api()
            report['api'] = api_status
            
            if api_status['running']:
                # Get models
                models_status = self.get_installed_models()
                report['models'] = models_status
                
                # Test Gemma if available
                if models_status['success'] and models_status['gemma_models']:
                    test_model = models_status['gemma_models'][0]['name']
                    test_result = self.test_gemma_model(test_model)
                    report['model_test'] = test_result
        
        return report