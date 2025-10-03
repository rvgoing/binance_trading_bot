
import os
import sys
from cryptography.fernet import Fernet
from pathlib import Path

class SecureConfig:
    def __init__(self, key_file='.encryption_key'):
        self.key_file = key_file
        self.cipher = self._load_or_create_key()
    
    def _load_or_create_key(self):
        """載入或建立加密金鑰"""
        if os.path.exists(self.key_file):
            # 載入現有金鑰
            with open(self.key_file, 'rb') as f:
                key = f.read()
            print("✓ Encryption key loaded")
        else:
            # 首次運行：生成新金鑰
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            
            # 設定檔案權限（僅擁有者可讀）
            os.chmod(self.key_file, 0o600)
            
            print("=" * 60)
            print("⚠️  NEW ENCRYPTION KEY GENERATED")
            print("=" * 60)
            print(f"Key saved to: {self.key_file}")
            print("\nIMPORTANT:")
            print("1. Backup this key file securely")
            print("2. Without it, you CANNOT decrypt your API keys")
            print("3. Add '.encryption_key' to .gitignore")
            print("=" * 60)
        
        return Fernet(key)
    
    def encrypt_string(self, plaintext):
        """加密字串"""
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt_string(self, encrypted_text):
        """解密字串"""
        try:
            return self.cipher.decrypt(encrypted_text.encode()).decode()
        except Exception as e:
            print(f"❌ Decryption failed: {e}")
            sys.exit(1)
    
    def save_encrypted_env(self, api_key, secret_key, mode='test'):
        """將加密後的 API Key 存入 .env.encrypted"""
        encrypted_api = self.encrypt_string(api_key)
        encrypted_secret = self.encrypt_string(secret_key)
        
        with open('.env.encrypted', 'w') as f:
            f.write(f"BINANCE_API_KEY_ENC={encrypted_api}\n")
            f.write(f"BINANCE_SECRET_KEY_ENC={encrypted_secret}\n")
            f.write(f"BINANCE_MODE={mode}\n")
        
        print("✓ API keys encrypted and saved to .env.encrypted")
        
        # 刪除明文 .env（如果存在）
        if os.path.exists('.env'):
            backup = '.env.backup_plaintext'
            os.rename('.env', backup)
            print(f"⚠️  Original .env moved to {backup}")
            print("   You should DELETE this file after verification")
    
    def load_decrypted_env(self):
        """從加密檔案載入並解密 API Key"""
        if not os.path.exists('.env.encrypted'):
            print("❌ .env.encrypted not found")
            print("   Run setup first: python secure_config.py --setup")
            sys.exit(1)
        
        with open('.env.encrypted', 'r') as f:
            lines = f.readlines()
        
        config = {}
        for line in lines:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                if key.endswith('_ENC'):
                    # 解密
                    original_key = key.replace('_ENC', '')
                    config[original_key] = self.decrypt_string(value)
                else:
                    config[key] = value
        
        return config

# CLI 工具：初次設定
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Secure API Key Manager')
    parser.add_argument('--setup', action='store_true', help='Setup encrypted API keys')
    parser.add_argument('--verify', action='store_true', help='Verify decryption')
    args = parser.parse_args()
    
    sc = SecureConfig()
    
    if args.setup:
        print("\n🔐 API Key Encryption Setup")
        print("-" * 60)
        
        api_key = input("Enter Binance API Key: ").strip()
        secret_key = input("Enter Binance Secret Key: ").strip()
        mode = input("Mode (test/live) [test]: ").strip() or 'test'
        
        if not api_key or not secret_key:
            print("❌ API keys cannot be empty")
            sys.exit(1)
        
        sc.save_encrypted_env(api_key, secret_key, mode)
        
        print("\n✅ Setup complete!")
        print("\nNext steps:")
        print("1. Add to .gitignore:")
        print("   .env.encrypted")
        print("   .encryption_key")
        print("2. Backup .encryption_key to secure location")
        print("3. Delete .env.backup_plaintext")
    
    elif args.verify:
        print("\n🔍 Verifying decryption...")
        config = sc.load_decrypted_env()
        
        print("\nDecrypted configuration:")
        print(f"  API Key: {config['BINANCE_API_KEY'][:10]}...{config['BINANCE_API_KEY'][-4:]}")
        print(f"  Secret:  {config['BINANCE_SECRET_KEY'][:10]}...{config['BINANCE_SECRET_KEY'][-4:]}")
        print(f"  Mode:    {config['BINANCE_MODE']}")
        print("\n✅ Decryption successful")
    
    else:
        parser.print_help()