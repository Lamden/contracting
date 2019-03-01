from decimal import Decimal


class Registry:

    @classmethod
    def register_class(cls, class_name, class_instance):
        setattr(cls, class_name, class_instance)

    @classmethod
    def get_data_type(cls, class_name):
        return getattr(cls, class_name)

    @classmethod
    def get_value_type(cls, value_type_name):
        value_type = {
            'int': Decimal,
            'float': Decimal,
            'Decimal': Decimal,
            'str': str,
            'bool': bool,
            'bytes': bytes,
            'tuple': eval,
            'dict': dict,
            'list': list
        }.get(value_type_name)
        assert value_type, 'DataType "{}" not found!'.format(value_type_name)
        return value_type