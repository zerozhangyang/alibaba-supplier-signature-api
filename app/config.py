from dataclasses import dataclass, field
import os


@dataclass
class Settings:
    # 服务配置
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "5772")))

    # 数据库连接（使用环境变量，不要把密码写在代码里）
    mysql_url: str = field(default_factory=lambda: os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1:3306/ali_supplier?charset=utf8mb4"
    ))

    supplier_id: str = field(default_factory=lambda: os.getenv("SUPPLIER_ID", "YOUR_SUPPLIER_ID"))

    # ========== 三方资源供应商密钥（由阿里云下发） ==========
    third_supplier_id: str = field(default_factory=lambda: os.getenv("THIRD_SUPPLIER_ID", "YOUR_THIRD_SUPPLIER_ID"))
    # 接收推送时用于解密的 AES 密钥
    third_decrypt_key: str = field(default_factory=lambda: os.getenv("THIRD_DECRYPT_KEY", "YOUR_32_CHAR_DECRYPT_KEY_HERE___"))
    third_decrypt_iv: str = field(default_factory=lambda: os.getenv("THIRD_DECRYPT_IV", "YOUR_16_CHAR_IV_"))
    # 向阿里云上传数据时用于加密的 AES 密钥
    third_upload_key: str = field(default_factory=lambda: os.getenv("THIRD_UPLOAD_KEY", "YOUR_32_CHAR_UPLOAD_KEY_HERE____"))
    third_upload_iv: str = field(default_factory=lambda: os.getenv("THIRD_UPLOAD_IV", "YOUR_16_CHAR_IV_"))
    # 阿里云接口地址（正式环境）
    third_callback_url: str = field(default_factory=lambda: os.getenv(
        "THIRD_CALLBACK_URL",
        "http://dysms-apicloud.cn-zhangjiakou.aliyuncs.com/dysms/supplier/register/v1/callback"
    ))
    third_submit_url: str = field(default_factory=lambda: os.getenv(
        "THIRD_SUBMIT_URL",
        "http://dysms-apicloud.cn-zhangjiakou.aliyuncs.com/dysms/supplier/register/v1/submit"
    ))
    third_query_url: str = field(default_factory=lambda: os.getenv(
        "THIRD_QUERY_URL",
        "http://dysms-apicloud.cn-zhangjiakou.aliyuncs.com/dysms/supplier/register/v1/query"
    ))

    # ========== 直连供应商密钥 ==========
    direct_supplier_id: str = field(default_factory=lambda: os.getenv("DIRECT_SUPPLIER_ID", ""))
    direct_aes_key: str = field(default_factory=lambda: os.getenv("DIRECT_AES_KEY", "YOUR_32_CHAR_DIRECT_AES_KEY_HERE"))
    direct_aes_iv: str = field(default_factory=lambda: os.getenv("DIRECT_AES_IV", "YOUR_16_CHAR_IV_"))
    # 直连回调地址（预发布环境）
    direct_callback_url: str = field(default_factory=lambda: os.getenv(
        "DIRECT_CALLBACK_URL",
        "http://pre-dysms-apicloud.cn-zhangjiakou.aliyuncs.com/dysms/supplier/register/v1/callback"
    ))


settings = Settings()
