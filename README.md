# 🔍 cekDNS — DNS & Mail Check Tool (Like IntoDNS)

**cekDNS** adalah aplikasi berbasis Django yang memungkinkan pengguna untuk memeriksa konfigurasi DNS domain secara mendalam seperti situs IntoDNS. Aplikasi ini mendukung pengecekan NS, SOA, MX, SPF, DKIM, DMARC, dan DNSSEC, serta menampilkan informasi TTL, IP server, status UP/Down, dan reverse lookup.

## 🌐 Fitur Utama

- Pengecekan struktur DNS (NS, SOA, A/AAAA, MX)
- Verifikasi DNSSEC
- Pemeriksaan SPF, DKIM, dan DMARC
- Reverse DNS
- Skor Kesehatan Domain (Health Score)
- Support Cloudflare Tunnel (akses internet tanpa expose IP)
- Output mirip tampilan IntoDNS

## 📸 Contoh Tampilan

- Tampilan awal: Form pencarian domain
- Halaman hasil: Tabel-tabel seperti IntoDNS, termasuk status dan informasi lengkap tiap record

## 🚀 Instalasi Lokal (Docker)

### 1. Clone repository ini

```bash
git clone https://github.com/ardantus/cekdns.git
cd cekdns
````

### 2. Siapkan `.env`

Buat file `.env` dan tambahkan token dari Cloudflare Tunnel (opsional):

```
CLOUDFLARED_TUNNEL_TOKEN=token_anda_dari_cloudflare
```

### 3. Jalankan dengan Docker Compose

```bash
docker-compose up -d --build
```

Akses di:

* Lokal: [http://localhost:8000/](http://localhost:8000/)
* Internet (jika menggunakan Cloudflare Tunnel): [https://cekdns.ardan.ovh/](https://cekdns.ardan.ovh/)

## 📁 Struktur Direktori

```
cekdns/
├── app/
│   ├── checker/
│   │   ├── templates/
│   │   │   └── checker/
│   │   │       ├── index.html
│   │   │       └── result.html
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── utils.py
│   ├── manage.py
│   └── ...
├── docker-compose.yml
├── Dockerfile
├── favicon.ico
└── README.md
```

## 🔐 Keamanan

* Gunakan `DEBUG=False` untuk produksi
* Tambahkan `ALLOWED_HOSTS` dan `CSRF_TRUSTED_ORIGINS` di `settings.py`:

  ```python
  ALLOWED_HOSTS = ['cekdns.ardan.ovh', 'localhost', '127.0.0.1']
  CSRF_TRUSTED_ORIGINS = ['https://cekdns.ardan.ovh']
  ```

## 💡 Tips Tambahan

* Pastikan favicon.ico berada di `/app/static/` dan di-serve melalui `urls.py` jika diperlukan.
* Untuk akses cepat:

  ```
  https://cekdns.ardan.ovh/google.com
  ```

## 📃 Lisensi

MIT License © 2025 Daffa Keyfaro / Ardan Wibowo

---
