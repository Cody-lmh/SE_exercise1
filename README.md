# NoteTaker - Personal Note Management Application

A modern, responsive web application for managing personal notes with a beautiful user interface and full CRUD functionality.

## 🌟 Features

- **Create Notes**: Add new notes with titles and rich content
- **Edit Notes**: Update existing notes with real-time editing
- **Delete Notes**: Remove notes you no longer need
- **Search Notes**: Find notes quickly by searching titles and content
- **Translate Notes**: Translate the content of the open note into Chinese (Simplified) with one click
- **Auto-save**: Notes are automatically saved as you type
- **Responsive Design**: Works perfectly on desktop and mobile devices
- **Modern UI**: Beautiful gradient design with smooth animations
- **Real-time Updates**: Instant feedback and updates

## 🚀 Live Demo

The application is deployed and accessible at: **https://3dhkilc88dkk.manus.space**

## 🛠 Technology Stack

### Frontend
- **HTML5**: Semantic markup structure
- **CSS3**: Modern styling with gradients, animations, and responsive design
- **JavaScript (ES6+)**: Interactive functionality and API communication

### Backend
- **Python Flask**: Web framework for API endpoints
- **Supabase Python client**: Data access through Supabase's PostgREST API
- **Flask-CORS**: Cross-origin resource sharing support

### Database
- **Supabase (PostgreSQL)**: Hosted Postgres reached through the Supabase client

## 📁 Project Structure

```
notetaking-app/
├── src/
│   ├── models/
│   │   ├── user.py          # User data access (Supabase)
│   │   └── note.py          # Note data access (Supabase)
│   ├── routes/
│   │   ├── user.py          # User API routes (template)
│   │   ├── note.py          # Note API endpoints
│   │   └── translate.py     # Translation API endpoint
│   ├── services/
│   │   └── translator.py    # OpenRouter translation client with MyMemory fallback
│   ├── static/
│   │   ├── index.html       # Frontend application
│   │   └── favicon.ico      # Application icon
│   ├── db.py                # Supabase client configuration
│   └── main.py              # Flask application entry point
├── supabase/
│   └── migrations/
│       └── 20250101000000_init_schema.sql  # notes/users tables, trigger, RLS policies
├── venv/                    # Python virtual environment
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🔧 Local Development Setup

### Prerequisites
- Python 3.11+
- pip (Python package manager)

### Installation Steps

1. **Clone or download the project**
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment**
   ```bash
   source venv/bin/activate
   ```

   Remark: On Windows, use `venv\Scripts\activate`

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Supabase**

   Create a project at [supabase.com](https://supabase.com), then open
   **SQL Editor → New query**, paste the contents of
   `supabase/migrations/20250101000000_init_schema.sql`, and run it. That creates
   the `notes` and `users` tables together with their access policies.

   Copy `.env.example` to `.env` and fill in the project URL and API key from
   **Project Settings → API**:
   ```bash
   cp .env.example .env
   ```

5. **Run the application**
   ```bash
   python src/main.py
   ```

6. **Access the application**
   - Open your browser and go to `http://localhost:5001`

## 📡 API Endpoints

### Notes API
- `GET /api/notes` - Get all notes
- `POST /api/notes` - Create a new note
- `GET /api/notes/<id>` - Get a specific note
- `PUT /api/notes/<id>` - Update a note
- `DELETE /api/notes/<id>` - Delete a note
- `GET /api/notes/search?q=<query>` - Search notes

### Translation API
- `POST /api/translate` - Translate text into a supported target language

Request body:
```json
{
  "content": "Hello, how are you?",
  "target_lang": "zh-CN"
}
```

Response:
```json
{
  "source_content": "Hello, how are you?",
  "translated_content": "你好，你好吗？",
  "target_lang": "zh-CN"
}
```

Supported `target_lang` values: `zh-CN` (Chinese, Simplified - default), `zh-TW` (Chinese, Traditional), `en` (English).

Translation prefers [OpenRouter](https://openrouter.ai/) whenever `OPENROUTER_API_KEY` is set, using the model named by `OPENROUTER_MODEL`. If the key is absent, or an OpenRouter request fails (rate limit, outage, bad model id), the request silently falls back to the free [MyMemory](https://mymemory.translated.net/) API, which needs no credentials; MyMemory input longer than 500 characters is chunked automatically. Only when both backends fail does `/api/translate` return `502`.

### Request/Response Format
```json
{
  "id": 1,
  "title": "My Note Title",
  "content": "Note content here...",
  "created_at": "2025-09-03T11:26:38.123456",
  "updated_at": "2025-09-03T11:27:30.654321"
}
```

## 🎨 User Interface Features

### Sidebar
- **Search Box**: Real-time search through note titles and content
- **New Note Button**: Create new notes instantly
- **Notes List**: Scrollable list of all notes with previews
- **Note Previews**: Show title, content preview, and last modified date

### Editor Panel
- **Title Input**: Edit note titles
- **Content Textarea**: Rich text editing area
- **Save Button**: Manual save option (auto-save also available)
- **Delete Button**: Remove notes with confirmation
- **Real-time Updates**: Changes reflected immediately

### Design Elements
- **Gradient Background**: Beautiful purple gradient backdrop
- **Glass Morphism**: Semi-transparent panels with backdrop blur
- **Smooth Animations**: Hover effects and transitions
- **Responsive Layout**: Adapts to different screen sizes
- **Modern Typography**: Clean, readable font stack

## 🔒 Database Schema

The schema is defined in [`supabase/migrations/20250101000000_init_schema.sql`](supabase/migrations/20250101000000_init_schema.sql)
and applied to the Supabase project (see the setup steps above).

### Notes Table
```sql
create table public.notes (
    id bigint generated by default as identity primary key,
    title varchar(200) not null,
    content text not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()  -- refreshed by the notes_set_updated_at trigger
);
```

### Users Table
```sql
create table public.users (
    id bigint generated by default as identity primary key,
    username varchar(80) not null unique,
    email varchar(120) not null unique
);
```

Because the app reaches the database through PostgREST with an API key, row
level security is enabled on both tables. The migration ships permissive
policies for the `anon` and `authenticated` roles since there are no end-user
accounts yet; replace them with user-scoped policies once authentication is added.

## 🚀 Deployment

The application is configured for easy deployment with:
- CORS enabled for cross-origin requests
- Host binding to `0.0.0.0` for external access
- Production-ready Flask configuration
- Supabase database (see the Vercel note below)

### ▲ Deploying to Vercel

The repository ships with a Vercel entrypoint at `api/index.py` and a `vercel.json`
that routes every request to the Flask app.

1. Install the CLI: `npm i -g vercel`
2. From the repository root, deploy:
   ```bash
   vercel         # preview deployment
   vercel --prod  # production deployment
   ```

Notes:
- `requirements.txt` at the repository root is installed automatically as the function's dependencies.
- Set `SUPABASE_URL` and `SUPABASE_KEY` in **Project Settings → Environment Variables**. Without them the API returns a configuration error.
- Translation only needs an API key for OpenRouter; without one it uses the free MyMemory API.
- Because data is stored in Supabase rather than on the function's filesystem, notes survive cold starts and scale out with the function.

## 🔧 Configuration

### Environment Variables
- `SUPABASE_URL`: Supabase project URL (Project Settings → API)
- `SUPABASE_KEY`: Supabase API key; the service-role key is recommended for server-side use
- `OPENROUTER_API_KEY`: OpenRouter API key; when set, translation uses OpenRouter instead of MyMemory
- `OPENROUTER_MODEL`: OpenRouter model id used for translation (defaults to `nvidia/nemotron-3-ultra-550b-a55b:free`)

Locally these are read from a `.env` file at the repository root; in production
set them in the deployment platform's dashboard.

### Database Configuration
- Supabase client configured in `src/db.py`
- Schema applied from `supabase/migrations/`
- No database file is created or read from the local filesystem

## 📱 Browser Compatibility

- Chrome/Chromium (recommended)
- Firefox
- Safari
- Edge
- Mobile browsers (iOS Safari, Chrome Mobile)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

For issues or questions:
1. Check the browser console for error messages
2. Verify the Flask server is running
3. Ensure all dependencies are installed
4. Check network connectivity for the deployed version

## 🎯 Future Enhancements

Potential improvements for future versions:
- User authentication and multi-user support
- Note categories and tags
- Rich text formatting (bold, italic, lists)
- File attachments
- Export functionality (PDF, Markdown)
- Dark/light theme toggle
- Offline support with service workers
- Note sharing capabilities

---

**Built with ❤️ using Flask, Supabase, and modern web technologies**

