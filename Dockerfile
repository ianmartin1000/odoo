FROM python:3.12-slim

# ── System dependencies needed to compile + run Odoo ──
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    libldap-dev \
    libsasl2-dev \
    libssl-dev \
    libjpeg-dev \
    libpq-dev \
    libffi-dev \
    zlib1g-dev \
    npm \
    node-less \
    xfonts-75dpi \
    xfonts-base \
    fontconfig \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g rtlcss

WORKDIR /opt/odoo

# ── Install Python dependencies from the repo's own requirements.txt ──
COPY requirements.txt .
RUN pip install --no-cache-dir setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# ── Copy the full source tree ──
COPY . .

EXPOSE 8069

CMD ["python", "odoo-bin", "-c", "/etc/odoo/odoo.conf"]
