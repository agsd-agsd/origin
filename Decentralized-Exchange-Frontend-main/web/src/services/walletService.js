// 钱包服务 - 处理区块链钱包的创建、存储和恢复
import CryptoJS from 'crypto-js';

// 用于生成随机数
function generateRandomBytes(length) {
  const array = new Uint8Array(length);
  window.crypto.getRandomValues(array);
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
}

// 简单实现的助记词生成（实际应用应使用BIP39标准）
const wordList = [
  'apple', 'banana', 'cat', 'dog', 'elephant', 'fish', 'goat', 'horse',
  'igloo', 'jacket', 'kite', 'lion', 'monkey', 'nest', 'orange', 'panda',
  'queen', 'rabbit', 'snake', 'tiger', 'umbrella', 'violin', 'whale', 'xylophone',
  'yellow', 'zebra', 'air', 'book', 'coin', 'door', 'eagle', 'fire', 'gold',
  'house', 'ice', 'jungle', 'key', 'lamp', 'moon', 'night', 'ocean', 'paper',
  'quiet', 'river', 'sun', 'tree', 'universe', 'voice', 'water', 'box', 'year', 'zone'
];

function generateMnemonic(strength = 128) {
  const wordCount = strength / 8;
  const indices = Array(wordCount).fill(0).map(() => Math.floor(Math.random() * wordList.length));
  return indices.map(index => wordList[index]).join(' ');
}

export default {
  // 创建新钱包
  createWallet() {
    // 生成私钥（简化版，实际应使用专业加密库）
    const privateKey = '0x' + generateRandomBytes(32);
    
    // 模拟从私钥导出公钥（简化版，实际应使用椭圆曲线算法）
    // 这里只是生成一个随机地址模拟公钥派生
    const address = '0x' + generateRandomBytes(20);
    
    // 生成助记词
    const mnemonic = generateMnemonic();
    
    return {
      privateKey,
      address,
      mnemonic
    };
  },
  
  // 从助记词恢复钱包
  recoverFromMnemonic(mnemonic) {
    // 实际应用应验证助记词并正确派生私钥
    // 这里简化处理，模拟恢复
    const privateKey = '0x' + CryptoJS.SHA256(mnemonic).toString();
    const address = '0x' + CryptoJS.SHA256(privateKey).toString().substring(0, 40);
    
    return {
      privateKey,
      address,
      mnemonic
    };
  },
  
  // 安全存储钱包信息
  secureStore(walletInfo, password) {
    // 加密整个钱包对象
    const encryptedData = CryptoJS.AES.encrypt(
      JSON.stringify({
        privateKey: walletInfo.privateKey,
        address: walletInfo.address,
        // 不存储助记词，用户应当自己保管
      }), 
      password
    ).toString();
    
    // 存储加密后的钱包数据和地址（地址不加密，用于识别）
    localStorage.setItem('encryptedWallet', encryptedData);
    localStorage.setItem('walletAddress', walletInfo.address);
    
    return true;
  },
  
  // 解锁钱包
  unlockWallet(password) {
    try {
      const encryptedData = localStorage.getItem('encryptedWallet');
      if (!encryptedData) return null;
      
      // 尝试解密
      const decrypted = CryptoJS.AES.decrypt(encryptedData, password).toString(CryptoJS.enc.Utf8);
      if (!decrypted) return null;
      
      return JSON.parse(decrypted);
    } catch (error) {
      console.error('解锁钱包失败:', error);
      return null; // 密码错误或数据损坏
    }
  },
  
  // 检查是否已有钱包
  hasWallet() {
    return !!localStorage.getItem('walletAddress');
  },
  
  // 验证密码强度
  validatePassword(password) {
    if (!password || password.length < 8) {
      return '密码至少需要8个字符';
    }
    
    // 简单的密码强度检查
    let strength = 0;
    if (/[a-z]/.test(password)) strength += 1;
    if (/[A-Z]/.test(password)) strength += 1;
    if (/[0-9]/.test(password)) strength += 1;
    if (/[^a-zA-Z0-9]/.test(password)) strength += 1;
    
    if (strength < 3) {
      return '密码需包含大小写字母、数字或特殊字符';
    }
    
    return null; // 密码有效
  }
}; 