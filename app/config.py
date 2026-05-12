from dataclasses import dataclass, field
import os


@dataclass
class Settings:
    # Server config
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "5772")))

    # Database
    mysql_url: str = field(default_factory=lambda: os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1:3306/ali_supplier?charset=utf8mb4"
    ))

    supplier_id: str = field(default_factory=lambda: os.getenv("SUPPLIER_ID", "YOUR_SUPPLIER_ID"))

    # Third-party supplier AES keys (provided by Alibaba)
    third_supplier_id: str = field(default_factory=lambda: os.getenv("THIRD_SUPPLIER_ID", "YOUR_THIRD_SUPPLIER_ID"))
    third_decrypt_key: str = field(default_factory=lambda: os.getenv("THIRD_DECRYPT_KEY", "YOUR_32_CHAR_DECRYPT_KEY_HERE___"))
    third_decrypt_iv: str = field(default_factory=lambda: os.getenv("THIRD_DECRYPT_IV", "YOUR_16_CHAR_IV_"))
    third_upload_key: str = field(default_factory=lambda: os.getenv("THIRD_UPLOAD_KEY", "YOUR_32_CHAR_UPLOAD_KEY_HERE____"))
    third_upload_iv: str = field(default_factory=lambda: os.getenv("THIRD_UPLOAD_IV", "YOUR_16_CHAR_IV_"))
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

    # Direct supplier AES keys
    direct_supplier_id: str = field(default_factory=lambda: os.getenv("DIRECT_SUPPLIER_ID", ""))
    direct_aes_key: str = field(default_factory=lambda: os.getenv("DIRECT_AES_KEY", "YOUR_32_CHAR_DIRECT_AES_KEY_HERE"))
    direct_aes_iv: str = field(default_factory=lambda: os.getenv("DIRECT_AES_IV", "YOUR_16_CHAR_IV_"))
    direct_callback_url: str = field(default_factory=lambda: os.getenv(
        "DIRECT_CALLBACK_URL",
        "http://pre-dysms-apicloud.cn-zhangjiakou.aliyuncs.com/dysms/supplier/register/v1/callback"
    ))


settings = Settings()
