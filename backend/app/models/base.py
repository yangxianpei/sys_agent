from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.inspection import inspect
Base =declarative_base()

class BaseModel(Base):
    __abstract__=True


    def to_dict(self,exclude=[],*args):
        result={}
        mapper = inspect(self.__class__)
        for column  in mapper.columns:
             # 获取列名
            col_name = column.name
            if col_name in exclude:
                continue
            # 获取此字段名的值
            value = getattr(self, col_name, None)
            # 如果value有是日期类型的话，调用isoformat转换为字符串
            if hasattr(value, "isoformat"):
                result[col_name] = value.isoformat() if value else None
            else:
                result[col_name] = value
        return result
        

    def __repr__(self) -> str:
        # 自动获取对象所有属性，不需要 __repr_fields__
        attrs = ", ".join(f"{k}={v}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({attrs})"