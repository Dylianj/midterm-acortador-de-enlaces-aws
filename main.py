from fastapi import FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import boto3
import uuid
import os
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  #debes limitar al dominio de S3/CloudFront
    allow_methods=["*"],
    allow_headers=["*"],
)
dynamodb = boto3.resource('dynamodb', region_name='us-east-1') 
table = dynamodb.Table('UrlShortener')

class URLCreate(BaseModel):
    original_url: str

# enlace corto
@app.post("/shorten")
def create_short_url(request: URLCreate):
    short_code = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    
    table.put_item(
        Item={
            'short_code': short_code,
            'original_url': request.original_url,
            'created_at': created_at
        }
    )
    
 #debes poner la ip publica de tu ec2
    host = os.getenv("API_HOST", "http://localhost:8000")
    
    return {
        "short_code": short_code,
        "original_url": request.original_url,
        "short_url": f"{host}/{short_code}"
    }

# redireccionar al destino
@app.get("/{short_code}")
def redirect_to_original(short_code: str):
    response = table.get_item(Key={'short_code': short_code})
    item = response.get('Item')
    
    if not item:
        raise HTTPException(status_code=404, detail="Not Found")
        
    return RedirectResponse(
        url=item['original_url'], 
        status_code=status.HTTP_307_TEMPORARY_REDIRECT
    )

# consultar información enlace
@app.get("/urls/{short_code}")
def get_url_info(short_code: str):
    response = table.get_item(Key={'short_code': short_code})
    item = response.get('Item')
    
    if not item:
        raise HTTPException(status_code=404, detail="Not Found")
        
    return item