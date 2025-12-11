# Secure Data Provider API

API REST modular con salida encriptada que permite consultar múltiples fuentes de datos de forma segura. Actualmente incluye integración completa con las APIs de Cloudflare (Trace y Geolocation).

## 🎯 Características

- ✅ **Arquitectura Modular**: Sistema de providers extensible para agregar nuevos servicios fácilmente
- 🔐 **Encriptación RSA-2048**: Todas las respuestas pueden encriptarse con RSA-OAEP + SHA-256
- 📦 **Múltiples Providers**: Sistema de registro de providers para servicios externos
- 🌐 **CORS Habilitado**: Acceso desde cualquier origen
- 📝 **Logging Completo**: Registro de todas las operaciones
- 💾 **Persistencia**: Guarda automáticamente consultas encriptadas y planas

## 🏗️ Arquitectura

### Componentes Principales

```
├── CryptoManager          # Gestión de encriptación RSA
├── BaseProvider           # Clase base abstracta para providers
├── CloudflareProvider     # Implementación para Cloudflare APIs
├── ProviderRegistry       # Registro centralizado de providers
└── REST Endpoints         # Endpoints de la API
```

### Agregar Nuevos Providers

Para agregar un nuevo provider, simplemente crea una clase que herede de `BaseProvider`:

```python
class MyCustomProvider(BaseProvider):
    def get_name(self) -> str:
        return "my_service"
    
    def get_version(self) -> str:
        return "1.0.0"
    
    def fetch_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Tu lógica aquí
        return {"data": "..."}
    
    def get_available_endpoints(self) -> List[Dict[str, str]]:
        return [{"type": "...", "description": "..."}]

# Registrar el provider
registry.register(MyCustomProvider())
```

## 📡 Endpoints Disponibles

### 1. Información General
```http
GET /
```

Retorna información sobre el servicio y endpoints disponibles.

### 2. Listar Providers
```http
GET /api/providers
```

Lista todos los providers disponibles y sus capacidades.

**Respuesta:**
```json
{
  "status": "success",
  "total_providers": 1,
  "providers": [
    {
      "name": "cloudflare",
      "version": "1.0.0",
      "endpoints": [...]
    }
  ]
}
```

### 3. Consulta Encriptada
```http
POST /api/query
Content-Type: application/json
```

**Body:**
```json
{
  "provider": "cloudflare",
  "params": {
    "query_type": "all"
  }
}
```

**Respuesta:**
```json
{
  "encrypted_data": ["base64chunk1", "base64chunk2", "..."],
  "sha256_hash": "hash...",
  "public_key_file": "public_key.pem",
  "note": "Use the private key to decrypt the data",
  "provider": "cloudflare"
}
```

### 4. Consulta Sin Encriptar
```http
POST /api/query/plain
Content-Type: application/json
```

**Body:**
```json
{
  "provider": "cloudflare",
  "params": {
    "query_type": "trace"
  }
}
```

**Respuesta:**
```json
{
  "status": "success",
  "timestamp": "2024-...",
  "provider": "cloudflare",
  "data": {
    "trace": {
      "success": true,
      "data": {
        "ip": "...",
        "loc": "US",
        "colo": "JFK",
        ...
      }
    }
  }
}
```

### 5. Descargar Llaves
```http
GET /api/keys/public
GET /api/keys/private
```

### 6. Health Check
```http
GET /api/health
```

## 🌐 Cloudflare Provider

El provider de Cloudflare soporta tres tipos de consultas:

### Tipos de Consulta

#### 1. Trace API
Obtiene información sobre IP, ubicación, TLS, HTTP version, etc.

```json
{
  "provider": "cloudflare",
  "params": {
    "query_type": "trace",
    "endpoint": "https://one.one.one.one/cdn-cgi/trace"  // opcional
  }
}
```

**Endpoints disponibles:**
- `https://one.one.one.one/cdn-cgi/trace`
- `https://1.0.0.1/cdn-cgi/trace`
- `https://cloudflare-dns.com/cdn-cgi/trace`
- `https://cloudflare-eth.com/cdn-cgi/trace`
- `https://workers.dev/cdn-cgi/trace`
- `https://pages.dev/cdn-cgi/trace`
- `https://cloudflare.tv/cdn-cgi/trace`
- `https://icanhazip.com/cdn-cgi/trace`

**Datos retornados:**
```
fl     - Cloudflare WebServer Instance
h      - WebServer Hostname
ip     - IP Address
ts     - Epoch Time (seconds.millis)
visit_scheme - https o http
uag    - User Agent
colo   - IATA location identifier
sliver - Request splitting status
http   - HTTP Version
loc    - Country Code (ISO 3166-1 alpha-2)
tls    - TLS/SSL Version
sni    - SNI encrypted or plaintext
warp   - Cloudflare Wireguard VPN status
gateway - Cloudflare Gateway status
rbi    - Remote Browser Isolation status
kex    - Key exchange method
```

#### 2. Geolocation API
Obtiene información detallada de geolocalización en formato JSON.

```json
{
  "provider": "cloudflare",
  "params": {
    "query_type": "geolocation"
  }
}
```

**Datos retornados:**
```json
{
  "hostname": "speed.cloudflare.com",
  "clientIp": "x.x.x.x",
  "httpProtocol": "HTTP/1.1",
  "asn": 13254,
  "asOrganization": "Organization Name",
  "colo": "JFK",
  "country": "US",
  "city": "New York City",
  "region": "New York",
  "postalCode": "10001",
  "latitude": "40.730610",
  "longitude": "-73.935242"
}
```

#### 3. Geolocation Headers
Obtiene información de geolocalización desde headers HTTP.

```json
{
  "provider": "cloudflare",
  "params": {
    "query_type": "geolocation_headers"
  }
}
```

**Headers retornados:**
```json
{
  "cf-meta-asn": "13254",
  "cf-meta-city": "New York City",
  "cf-meta-colo": "JFK",
  "cf-meta-country": "US",
  "cf-meta-ip": "x.x.x.x",
  "cf-meta-latitude": "40.730610",
  "cf-meta-longitude": "-73.935242",
  "cf-meta-postalcode": "10001",
  "cf-meta-request-time": "1724183717263",
  "cf-meta-timezone": "America/New_York"
}
```

#### 4. Todo (All)
Obtiene información de todos los tipos anteriores en una sola consulta.

```json
{
  "provider": "cloudflare",
  "params": {
    "query_type": "all",
    "timeout": 15
  }
}
```

### Parámetros Opcionales

- `timeout`: Timeout en segundos para las peticiones (default: 10)
- `endpoint`: URL específica para el trace (solo para query_type "trace")

## 🔍 Censys Provider

El provider de Censys permite buscar y analizar dispositivos conectados a Internet. **Requiere una API key de Censys.**

### Obtener API Key

1. Crea una cuenta en [Censys](https://account.censys.io/register)
2. Obtén tu API key desde [tu perfil](https://account.censys.io/)
3. Configura la variable de entorno `CENSYS_API_KEY`

### Tipos de Consulta

#### 1. My IP Info (Integración Cloudflare + Censys)
Obtiene tu IP desde Cloudflare Trace y luego consulta información detallada en Censys.

```json
{
  "provider": "censys",
  "params": {
    "query_type": "myip_info"
  }
}
```

**Respuesta incluye:**
- IP detectada por Cloudflare
- Información completa de Cloudflare Trace
- Información detallada de Censys sobre tu IP (puertos, servicios, vulnerabilidades)

#### 2. Host Information
Obtiene información completa sobre una IP específica.

```json
{
  "provider": "censys",
  "params": {
    "query_type": "host_info",
    "ip": "8.8.8.8",
    "history": false,
    "minify": false
  }
}
```

**Parámetros:**
- `ip`: Dirección IP a consultar (requerido)
- `history`: Incluir información histórica (opcional)
- `minify`: Solo puertos e información general (opcional)

**Datos retornados:**
- Puertos abiertos
- Servicios detectados
- Organización/ISP
- Ubicación geográfica
- Vulnerabilidades conocidas
- Banners de servicios

#### 3. Host Search
Busca dispositivos usando los filtros de Censys.

```json
{
  "provider": "censys",
  "params": {
    "query_type": "host_search",
    "query": "apache country:US",
    "facets": "org,os",
    "page": 1
  }
}
```

**Filtros populares:**
- `country:US` - País
- `city:"New York"` - Ciudad
- `org:Google` - Organización
- `port:80` - Puerto específico
- `product:nginx` - Producto/Software
- `os:Windows` - Sistema operativo
- `vuln:CVE-2021-44228` - Vulnerabilidad específica

**Facets disponibles:**
```
asn, city, country, domain, isp, link, org, os, port, product, state, version, vuln
```

#### 4. Host Count
Cuenta resultados sin consumir créditos de query.

```json
{
  "provider": "censys",
  "params": {
    "query_type": "host_count",
    "query": "apache country:DE",
    "facets": "org:5"
  }
}
```

#### 5. DNS Resolve
Convierte hostnames a direcciones IP.

```json
{
  "provider": "censys",
  "params": {
    "query_type": "dns_resolve",
    "hostnames": "google.com,facebook.com,twitter.com"
  }
}
```

#### 6. DNS Reverse
Reverse DNS lookup (IP a hostname).

```json
{
  "provider": "censys",
  "params": {
    "query_type": "dns_reverse",
    "ips": "8.8.8.8,1.1.1.1"
  }
}
```

#### 7. My IP
Obtiene solo tu IP pública (método simple de Censys).

```json
{
  "provider": "censys",
  "params": {
    "query_type": "myip"
  }
}
```

#### 8. Account Profile
Información de tu cuenta Censys.

```json
{
  "provider": "censys",
  "params": {
    "query_type": "account_profile"
  }
}
```

#### 9. API Info
Información sobre tu plan API y créditos disponibles.

```json
{
  "provider": "censys",
  "params": {
    "query_type": "api_info"
  }
}
```

### Créditos API

Censys usa dos tipos de créditos:

**Query Credits:**
- Búsquedas con filtros
- Acceso a resultados más allá de la primera página
- Host information

**Scan Credits:**
- Escaneos bajo demanda (no implementados en este provider)

**Consultas gratuitas:**
- Host count
- DNS resolve/reverse
- My IP
- Account profile
- API info

### Ejemplos de Queries de Búsqueda

```python
# Webcams expuestas
"title:\"Network Camera\" port:80"

# Bases de datos MongoDB sin autenticación
"product:MongoDB port:27017 -authentication"

# Servicios con vulnerabilidades críticas
"vuln:CVE-2021-44228"

# Dispositivos IoT específicos
"product:\"Raspberry Pi\""

# Servidores SSH por país
"port:22 country:US"

# Apache en versión específica
"apache/2.4.49 country:BR"
```

### Parámetros Opcionales

- `timeout`: Timeout en segundos para las peticiones (default: 30)

## 💡 Caso de Uso: Análisis de Seguridad con Cloudflare + Censys

Ejemplo de flujo completo:

```bash
# 1. Obtener tu IP y analizar con Censys
curl -X POST http://localhost:5000/api/query/plain \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "censys",
    "params": {
      "query_type": "myip_info"
    }
  }'
```

Esto te dará:
1. Tu IP real (desde Cloudflare)
2. Ubicación y metadatos (desde Cloudflare)
3. Puertos abiertos en tu IP (desde Censys)
4. Servicios expuestos (desde Censys)
5. Vulnerabilidades conocidas (desde Censys)

### Parámetros Opcionales

- `timeout`: Timeout en segundos para las peticiones (default: 10)
- `endpoint`: URL específica para el trace (solo para query_type "trace")

## 🔐 Encriptación

### Generación de Llaves

Al iniciar, el servidor genera automáticamente un par de llaves RSA-2048:
- `private_key.pem` - Para desencriptar
- `public_key.pem` - Para verificar

### Desencriptación

Para desencriptar los datos:

```python
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import base64
import json

# Cargar llave privada
with open("private_key.pem", "rb") as f:
    private_key = serialization.load_pem_private_key(
        f.read(),
        password=None,
        backend=default_backend()
    )

# Desencriptar chunks
decrypted_chunks = []
for chunk in encrypted_data:
    decrypted = private_key.decrypt(
        base64.b64decode(chunk),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    decrypted_chunks.append(decrypted.decode())

# Reconstruir JSON
json_data = ''.join(decrypted_chunks)
data = json.loads(json_data)
```

## 🚀 Instalación

### Requisitos

```bash
pip install flask flask-cors cryptography requests
```

### Ejecutar

```bash
python app.py
```

El servidor iniciará en `http://0.0.0.0:5000`

## 📝 Ejemplos de Uso

### cURL

#### Obtener información de Cloudflare (encriptado)
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "cloudflare",
    "params": {
      "query_type": "all"
    }
  }'
```

#### Obtener información de Cloudflare (sin encriptar)
```bash
curl -X POST http://localhost:5000/api/query/plain \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "cloudflare",
    "params": {
      "query_type": "trace"
    }
  }'
```

#### Listar providers disponibles
```bash
curl http://localhost:5000/api/providers
```

### Python

```python
import requests

# Consulta encriptada
response = requests.post('http://localhost:5000/api/query', json={
    "provider": "cloudflare",
    "params": {
        "query_type": "all",
        "timeout": 15
    }
})

encrypted_result = response.json()
print(f"Hash SHA-256: {encrypted_result['sha256_hash']}")

# Consulta sin encriptar
response = requests.post('http://localhost:5000/api/query/plain', json={
    "provider": "cloudflare",
    "params": {
        "query_type": "geolocation"
    }
})

plain_result = response.json()
print(json.dumps(plain_result, indent=2))
```

### JavaScript/Node.js

```javascript
// Consulta con fetch
const response = await fetch('http://localhost:5000/api/query/plain', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    provider: 'cloudflare',
    params: {
      query_type: 'trace'
    }
  })
});

const data = await response.json();
console.log(data);
```

## 📂 Estructura de Archivos

```
/mnt/shared_data/
├── private_key.pem                    # Llave privada RSA
├── public_key.pem                     # Llave pública RSA
├── query_cloudflare_20241205_143022.json  # Consultas guardadas
└── ...
```

Cada consulta encriptada se guarda con:
- Datos encriptados
- Hash SHA-256
- Datos en texto plano (para referencia)

## 🔧 Configuración

### Variables de Entorno

```bash
# Puerto del servidor (opcional)
export PORT=5000

# Nivel de logging (opcional)
export LOG_LEVEL=INFO
```

### Directorios

- Output: `/mnt/shared_data/` - Donde se guardan llaves y consultas

## 🌐 IP-API Provider

El provider de IP-API.com permite obtener geolocalización detallada de cualquier IP. **No requiere API key** - es completamente gratuito con rate limit de 45 requests/minuto.

### Características

- ✅ **Gratuito** - No requiere API key
- ✅ **Rate limit generoso** - 45 requests/minuto
- ✅ **Batch support** - Hasta 100 IPs por petición
- ✅ **Multi-idioma** - Soporta 8 idiomas
- ✅ **Detección avanzada** - Proxy, hosting, móvil

### Tipos de Consulta

#### 1. Lookup (IP Específica)
```json
{
  "provider": "ipapi",
  "params": {
    "query_type": "lookup",
    "ip": "8.8.8.8"
  }
}
```

#### 2. Lookup Own IP
```json
{
  "provider": "ipapi",
  "params": {
    "query_type": "lookup_own"
  }
}
```

#### 3. Lookup with Cloudflare
```json
{
  "provider": "ipapi",
  "params": {
    "query_type": "lookup_with_cloudflare"
  }
}
```

#### 4. Batch Lookup (hasta 100 IPs)
```json
{
  "provider": "ipapi",
  "params": {
    "query_type": "batch",
    "ips": ["8.8.8.8", "1.1.1.1", "208.67.222.222"]
  }
}
```

### Campos Disponibles

```
status, message, continent, continentCode, country, countryCode,
region, regionName, city, district, zip, lat, lon, timezone,
offset, currency, isp, org, as, asname, reverse, mobile,
proxy, hosting, query
```

### Idiomas Soportados

`en`, `de`, `es`, `pt-BR`, `fr`, `ja`, `zh-CN`, `ru`

## ⭐ Workflow Integrado: Cloudflare → IP-API → Censys

Endpoint especial que ejecuta un análisis completo en una sola petición:

```bash
POST /api/query/integrated
```

**Request:**
```json
{
  "include_censys": true,
  "ipapi_fields": ["country", "city", "isp"],
  "ipapi_lang": "es"
}
```

**Flujo de ejecución:**
1. **Cloudflare Trace** - IP real y metadatos de conexión
2. **IP-API** - Geolocalización detallada  
3. **Censys** - Análisis de seguridad (opcional)

**Respuesta incluye:**
- IP detectada
- Información de Cloudflare (TLS, HTTP, data center)
- Geolocalización completa (país, ciudad, coordenadas, ISP)
- Análisis Censys (puertos, servicios, vulnerabilidades)
- Resumen consolidado

## 🔍 SerpStack Provider - Punto de Entrada Principal

El provider de SerpStack permite buscar en Google y extraer información de resultados SERP (Search Engine Results Pages). **Requiere API key** - plan gratuito disponible con 100 requests/mes.

### Características

- ✅ **Búsqueda en Google** - SERP scraping en tiempo real
- ✅ **Extracción de URLs** - URLs orgánicas y anuncios
- ✅ **Extracción de dominios** - Dominios únicos de resultados
- ✅ **Geolocalización** - Búsquedas desde diferentes ubicaciones
- ✅ **Multi-dispositivo** - Desktop, mobile, tablet
- ✅ **CAPTCHA solving** - Manejo automático de CAPTCHAs

### Tipos de Consulta

#### 1. Búsqueda Básica
```json
{
  "provider": "serpstack",
  "params": {
    "query_type": "search",
    "query": "python programming",
    "num": 10
  }
}
```

#### 2. Extraer URLs
```json
{
  "provider": "serpstack",
  "params": {
    "query_type": "extract_urls",
    "query": "cloud computing",
    "num": 10,
    "include_ads": false
  }
}
```

#### 3. Extraer Dominios
```json
{
  "provider": "serpstack",
  "params": {
    "query_type": "extract_domains",
    "query": "amazon aws"
  }
}
```

### Parámetros Avanzados

- `location`: Ubicación geográfica (ej: "United States", "Mexico")
- `device`: Tipo de dispositivo ("desktop", "mobile", "tablet")
- `gl`: Código de país (ej: "us", "mx", "es")
- `num`: Número de resultados (máx 100)

## 🌟 Workflow Completo: SerpStack → DNS → Análisis Integral

### Endpoint Principal: `/api/search/analyze`

Este es el **punto de entrada recomendado** de toda la API. Una sola petición que ejecuta el flujo completo:

```bash
POST /api/search/analyze
```

**Request Body:**
```json
{
  "query": "amazon.com",           // requerido: búsqueda
  "num_results": 5,                // opcional: resultados SERP (default: 5)
  "analyze_top": 3,                // opcional: analizar top N dominios (default: 3)
  "include_censys": true,          // opcional: análisis Censys (default: true)
  "location": "United States",     // opcional: ubicación de búsqueda
  "ipapi_lang": "en"               // opcional: idioma para IP-API (default: "en")
}
```

### Flujo de Ejecución Completo

```
1. SerpStack SERP Search
   ↓
   Búsqueda: "amazon.com"
   Resultados: amazon.com, aws.amazon.com, primevideo.com...
   
2. Extracción de Dominios
   ↓
   Dominios únicos encontrados
   
3. Resolución DNS
   ↓
   amazon.com → 54.239.28.85
   aws.amazon.com → 52.94.236.248
   
4. Análisis Paralelo (para cada IP)
   ├─► Cloudflare Trace
   │   └─► Verifica conectividad
   │   └─► Metadata de conexión
   │
   ├─► IP-API Geolocation
   │   └─► País, ciudad, región
   │   └─► ISP, organización
   │   └─► Coordenadas GPS
   │   └─► Zona horaria
   │
   └─► Censys Analysis (opcional)
       └─► Puertos abiertos
       └─► Servicios detectados
       └─► Vulnerabilidades
       └─► Banners

5. Reporte Consolidado
   ↓
   JSON unificado con todos los datos
```

### Ejemplo de Uso

```bash
curl -X POST http://localhost:5000/api/search/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "github.com",
    "num_results": 5,
    "analyze_top": 2,
    "include_censys": true
  }'
```

### Ejemplo de Respuesta

```json
{
  "status": "success",
  "timestamp": "2024-12-05T...",
  "workflow": "SerpStack → DNS → Cloudflare → IP-API → Censys",
  "query": "github.com",
  "serpstack": {
    "success": true,
    "total_domains": 10,
    "domains": [
      {
        "domain": "github.com",
        "title": "GitHub: Let's build from here",
        "first_seen_position": 1
      }
    ]
  },
  "analysis": [
    {
      "domain": "github.com",
      "title": "GitHub: Let's build from here",
      "position": 1,
      "ip": "140.82.113.4",
      "dns_resolved": true,
      "geolocation": {
        "country": "United States",
        "city": "San Francisco",
        "isp": "GitHub, Inc.",
        "org": "GitHub, Inc.",
        "lat": 37.7749,
        "lon": -122.4194,
        "timezone": "America/Los_Angeles"
      },
      "censys": {
        "ports": [22, 80, 443],
        "services_count": 3,
        "org": "GitHub, Inc.",
        "hostnames": ["lb-140-82-113-4-iad.github.com"]
      }
    }
  ],
  "summary": {
    "query": "github.com",
    "total_serp_results": 10,
    "domains_analyzed": 2,
    "domains_with_ip": 2,
    "countries": ["United States"],
    "total_open_ports": 6
  }
}
```

### Casos de Uso del Workflow

#### 1. Investigación de Competencia
```bash
# Analizar dónde está hospedada la competencia
curl -X POST /api/search/analyze -d '{"query": "competitor.com", "analyze_top": 5}'
```

#### 2. Auditoría de Seguridad
```bash
# Identificar puertos abiertos en infraestructura
curl -X POST /api/search/analyze -d '{"query": "mycompany.com", "include_censys": true}'
```

#### 3. Mapeo de Infraestructura
```bash
# Descubrir todos los dominios relacionados
curl -X POST /api/search/analyze -d '{"query": "amazon", "num_results": 20}'
```

#### 4. Análisis Geográfico
```bash
# Ver distribución geográfica de servicios
curl -X POST /api/search/analyze -d '{"query": "cdn provider", "location": "Germany"}'
```

### Ventajas del Workflow Completo

✅ **Una sola petición** - Todo el análisis en un request  
✅ **Automático** - No necesitas ejecutar pasos manualmente  
✅ **Completo** - SERP + DNS + Geo + Seguridad  
✅ **Escalable** - Analiza múltiples dominios simultáneamente  
✅ **Flexible** - Activa/desactiva providers según necesites

### Requerimientos

| Provider | Requerido | API Key | Costo |
|----------|-----------|---------|-------|
| SerpStack | ✅ Sí | Sí | 100/mes gratis |
| Cloudflare | ❌ No | No | Gratis |
| IP-API | ❌ No | No | Gratis (45/min) |
| Censys | ❌ No | Sí | 100/mes gratis |

**Mínimo para funcionar:** Solo SERPSTACK_API_KEY  
**Recomendado:** SERPSTACK_API_KEY + CENSYS_API_KEY

## 🛣️ Roadmap

### Providers Actuales

- ✅ **SerpStack** (Google SERP Scraping) - PUNTO DE ENTRADA
- ✅ Cloudflare (Trace + Geolocation)
- ✅ IP-API (Free Geolocation - No API Key Required)
- ✅ **Censys** (Internet-wide Search Engine - 3.4B+ services)
- ✅ **PeeringDB** (🆓 Free Peering Database - No API Key Required)
- ✅ **Workflow Completo** - SerpStack → DNS → Cloudflare → IP-API → Censys → PeeringDB

### Flujo de Trabajo v2.5.0

```
Usuario ingresa búsqueda
         ↓
    SerpStack
  (Busca en Google)
         ↓
  Extrae Dominios
         ↓
   Resuelve DNS
         ↓
    ┌────┴────┬────────┬────────┬──────────┐
    ↓         ↓        ↓        ↓          ↓
Cloudflare  IP-API  Censys  PeeringDB  Análisis
    ↓         ↓      (ASN)   (Red Info)   ↓
    └────┬────┴────────┴────────┴──────────┘
         ↓
  Reporte Consolidado Enriquecido
```

### 🆕 PeeringDB Integration

**Activación Automática:**
Cuando Censys detecta un ASN, PeeringDB se consulta automáticamente para enriquecer con:
- Nombre y organización de la red
- Política de peering (Open/Selective/Restrictive)
- Presencias en IXPs (Internet Exchange Points)
- Presencias en facilities/data centers
- Nivel de tráfico y prefijos IPv4/IPv6

**Ventajas:**
- ✅ Completamente gratuito
- ✅ Sin API key requerida
- ✅ Sin límites de consultas
- ✅ Integración automática

### Próximos Providers

- [ ] IPInfo Provider
- [ ] MaxMind GeoIP Provider
- [ ] Custom API Provider (genérico)
- [ ] Database Provider (PostgreSQL/MySQL)
- [ ] Cache Provider (Redis)

### Mejoras Planeadas

- [ ] Autenticación JWT
- [ ] Rate limiting
- [ ] Métricas y monitoreo
- [ ] WebSocket support
- [ ] Docker container
- [ ] API documentation con Swagger/OpenAPI

## 📄 Licencia

Este proyecto está bajo licencia MIT.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Para agregar un nuevo provider:

1. Crea una clase que herede de `BaseProvider`
2. Implementa los métodos abstractos requeridos
3. Registra tu provider en `registry.register(TuProvider())`
4. Documenta el uso en este README

## 📞 Soporte

Para reportar issues o solicitar features, por favor abre un issue en el repositorio.

---

**Versión:** 2.0.0  
**Última actualización:** Diciembre 2024
#Calupoh_OSINT_API
