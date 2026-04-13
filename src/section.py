import ast
from typing import Dict, Literal
from dataclasses import dataclass

@dataclass
class EnvClass:
    urls: Dict
    algorithm: Literal['round_robin', 'weighted', 'least_connections']
    proxy_timeout: float
    proxy_max_retries: int

    @classmethod
    def from_dict(cls, data: dict):
        raw_urls = data.get('urls', '{}')
        
        # Traitement de la chaîne avec guillemets simples
        if isinstance(raw_urls, str):
            try:
                # ast.literal_eval est parfait pour "{'key': 'value'}"
                urls_dict = ast.literal_eval(raw_urls)
            except (ValueError, SyntaxError):
                urls_dict = {}
        else:
            urls_dict = raw_urls
        

        return cls(
            urls=urls_dict,
            algorithm=data.get('algorithm', 'round_robin'),
            proxy_timeout= float(data.get('proxy_timeout', 30.0)),
            proxy_max_retries= int(data.get('proxy_max_retries', 3))
        )
