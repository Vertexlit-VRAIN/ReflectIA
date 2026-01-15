# metrics/lexicon_ca.py
"""
Catalan Lexicons for Design and Technology analysis.
Used to compute Technical Knowledge and Specificity metrics.
"""

# Broad Technical Terms (General Design Knowledge)
TECHNICAL_TERMS_CA = {
    "disseny", "color", "imatge", "text", "forma", "fons", "estil", 
    "art", "gràfic", "visual", "projecte", "idea", "concepte", "creatiu",
    "dibuix", "esbós", "maqueta", "presentació", "arxiu", "document",
    "pàgina", "web", "digital", "paper", "llapis", "tinta", "quadre",
    "foto", "fotografia", "pintura", "il·lustració", "video", "àudio",
    "mida", "gran", "petit", "ample", "alt", "mesura", "proposta",
    "referència", "inspiració", "moda", "tendència", "marca", "logo",
    "icona", "símbol", "lletra", "font", "tipus", "títol", "cos",
    "espai", "blanc", "negre", "blau", "vermell", "groc", "verd",
    "bocet", "esborrany", "final", "entrega", "client", "usuari",
    "briefing", "target", "objectiu", "missatge", "comunicació"
}

# Specific / Concrete Design Terms (Depth)
SPECIFIC_TERMS_CA = {
    # Typography
    "tipografia", "serif", "sans-serif", "pal sec", "romana", "cursiva", 
    "negreta", "versaleta", "interlineatge", "kerning", "tracking", 
    "lligadura", "glif", "ascendent", "descendent", "ull", "remat", 
    "caixa", "alta", "baixa", "família", "font", "lletra", "legibilitat",
    "llegibilitat", "paràgraf", "alineació", "justificat", "esquerra", 
    "dreta", "centrat", "orfe", "vídua", "riu", "taca",
    
    # Layout & Grid
    "reticle", "graella", "jerarquia", "composició", "contrast", "equilibri", 
    "pes", "tensió", "ritme", "repetició", "proporció", "escala", "aire",
    "respirar", "marge", "columna", "mitjanit", "carrer", "gutter", 
    "sagnat", "sang", "tall", "troquel", "plec", "díptic", "tríptic", 
    "fulletó", "cartell", "pòster", "bànner", "capçalera", "peu", "foli",
    "numeració", "secció", "capítol",
    
    # Color & Image
    "cmyk", "rgb", "pantone", "hex", "hexadecimal", "saturació", "lluentor", 
    "matís", "to", "valor", "gamut", "perfil", "calibració", "vector", 
    "píxel", "mapa", "bits", "ràster", "resolució", "dpi", "ppi", "72ppp", 
    "300ppp", "interpolació", "compressió", "jpg", "png", "svg", "pdf", 
    "tiff", "gif", "psd", "ai", "indd", "raw", "exposició", "enfocament", 
    "profunditat", "camp", "balanç", "blancs", "historial", "filtre", 
    "màscara", "capa", "canal", "traç", "farciment", "degradat", "opacitat", 
    "fusió", "vectorial", "bitmap",
    
    # Branding & UX/UI
    "branding", "identitat", "corporativa", "logotip", "isotip", "imagotip", 
    "isologotip", "manual", "normativa", "aplicació", "papereria", 
    "targeta", "sobre", "carpeta", "senyalètica", "envàs", "packaging", 
    "etiqueta", "interfície", "ui", "ux", "experiència", "wireframe", 
    "prototip", "navegació", "menú", "botó", "crida", "acció", "cta", 
    "responsive", "adaptatiu", "accessibilitat", "usabilitat", "test"
}
