# 🎓 Dashboard Estudiante

Este proyecto es un **sistema de estudiante** desarrollado con **React + Vite**.  
Incluye un **sidebar lateral** y un **header superior** fijos, mientras que el contenido central cambia dinámicamente según la sección seleccionada.

---

## 🚀 Tecnologías usadas
- [React](https://react.dev/) – Librería para construir interfaces de usuario.
- [Vite](https://vitejs.dev/) – Bundler ultrarrápido para desarrollo moderno en frontend.
- [React Router DOM](https://reactrouter.com/) – Navegación entre páginas (SPA).
- CSS (estilos personalizados).

---

## 📂 Estructura de carpetas

estudiante-dashboard/
├── public/              # Archivos estáticos
├── src/
│   ├── assets/          # Imágenes y recursos
│   ├── components/      # Componentes reutilizables (Sidebar, Header)
│   ├── layouts/         # Layout principal (estructura base)
│   ├── pages/           # Páginas (Home, Perfil, Talleres, etc.)
│   ├── styles/          # Archivos CSS globales
│   ├── App.jsx          # Rutas principales
│   └── main.jsx         # Punto de entrada de React
├── index.html           # Documento HTML base
├── package.json         # Dependencias y scripts
├── vite.config.js       # Configuración de Vite
└── README.md            # Este archivo


---

## 📦 Instalación

1. Clonar el repositorio o crear el proyecto con Vite:

   ```bash
   npm create vite@latest estudiante-dashboard -- --template react
   ```

2. Entrar al directorio del proyecto:

   ```bash
   cd estudiante-dashboard
   ```

3. Instalar dependencias:

   ```bash
   npm install
   ```

4. Instalar React Router (para manejar las páginas):

   ```bash
   npm install react-router-dom
   npm install react-icons
   ```

---

## ▶️ Ejecución en modo desarrollo

```bash
npm run dev
```

Esto abrirá la aplicación en:  
👉 `http://localhost:5173/` (puerto por defecto de Vite).

---

## 🏗️ Build para producción

```bash
npm run build
```

El resultado optimizado se guardará en la carpeta `dist/`.

Para previsualizar el build:

```bash
npm run preview
```

---

## 📌 Funcionalidades actuales
- **Sidebar fijo** con navegación entre secciones.
- **Header superior** con datos del estudiante.
- **Contenido dinámico** (Home, Perfil, Talleres, Asistencias, Cursos, Calificaciones, Certificaciones).
- Estilos básicos en `global.css`.

---

## 📖 Próximos pasos
- Conectar el sistema a una API para datos reales (ejemplo: calificaciones desde base de datos).
- Implementar login (correo institucional o Gmail).
- Mejorar el diseño con librerías como TailwindCSS o Material UI.
- Añadir soporte responsive completo para móviles.

---

## 👨‍💻 Autor
Proyecto académico desarrollado con fines de práctica para la creación de un **Dashboard Estudiantil** en React + Vite.