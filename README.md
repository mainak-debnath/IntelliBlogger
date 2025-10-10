## 📝 IntelliBlogger: AI-Powered YouTube to Blog Converter

Transform YouTube videos into engaging, professional blog posts in seconds with AI-powered content generation.

## Demo
### Homepage
https://github.com/user-attachments/assets/8bb5edc6-bc26-493d-affb-169f0ce310ad

### Login
https://github.com/user-attachments/assets/6e053f0b-0cff-4e25-b5ac-8d195842ae29
### Signup
https://github.com/user-attachments/assets/39562859-fa05-4552-836c-361bbf0229c2
### Blog generator
https://github.com/user-attachments/assets/83418401-2266-4a95-a8df-0bf3e90a0a07
### Saved blogs page

###Blog details and editing

## 🎯 What is IntelliBlogger?

IntelliBlogger converts any YouTube video into a well-written blog post using AI. Perfect for content creators, marketers, and educators who want to repurpose video content into written format.

**Simply paste a YouTube link, choose your style, and get a publish-ready blog post.**

## ✨ Features

### 🎥 Smart Conversion

- Paste any YouTube link and get a complete blog post
- Choose your writing style: Professional, Casual, Witty, or Technical
- Select content length: Short, Medium, or Long

### ✍️ Edit & Customize

- Built-in rich text editor to refine your content
- Edit titles and content with ease
- Real-time preview of your changes

### 📚 Organize Your Content

- Save blogs to your personal dashboard
- Search and filter your saved posts
- Access your content anytime

### 📤 Export & Share

- **Download:** PDF, Markdown, or HTML format
- **Share:** Directly to LinkedIn, Twitter, or Email
- **Copy:** One-click clipboard copy

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Node.js 18 or higher
- Redis (for caching)
- FFmpeg (for audio processing)

### Installation

1.  **Clone the repository**

```bash
git clone https://github.com/mainak-debnath/IntelliBlogger.git
cd IntelliBlogger
```

1.  **Setup Backend**

```bash
cd Backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

1.  **Configure Environment** Create `.env` file in the Backend directory:

```bash
SECRET_KEY=your-secret-key
GEMINI_API_KEY=your-gemini-api-key
ASSEMBLY_API_KEY=your-assemblyai-api-key
```

1.  **Setup Database**

```bash
python manage.py migrate
```

1.  **Start Backend**

```bash

python manage.py runserver
```

1.  **Setup Frontend** (new terminal)

```bash
cd Frontend
npm install
npm start
```

1.  **Access the app** at http://localhost:4200

## 💡 How to Use

1.  **Sign up** for a free account
2.  **Paste** any YouTube video link
3.  **Choose** your preferred tone and length
4.  **Generate** your blog post
5.  **Edit** content using the rich text editor
6.  **Export** or share your finished blog

## 🛠️ Tech Stack

- **Frontend:** Angular, TypeScript
- **Backend:** Django, Python
- **AI:** Google Gemini, AssemblyAI
- **Database:** SQLite

- **⚠️ Current Limitations**

  - Only English audio is supported at this time
  - Videos must have clear audio (automated captions may not work well)

## 🗺️ Project Roadmap

IntelliBlogger is continuously evolving. Here are some of our planned features and improvements:

- **Future Enhancements:**

  - Direct publishing integrations with popular CMS platforms (WordPress, Medium).
  - Advanced content analytics and performance tracking.
  - Mobile application for on-the-go content generation.
  - Enhanced UI/UX for a more intuitive user experience.
