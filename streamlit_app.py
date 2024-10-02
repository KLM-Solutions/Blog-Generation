import os
import streamlit as st
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up OpenAI API
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Set up Google Cloud credentials
SCOPES = ['https://www.googleapis.com/auth/blogger']
BLOG_ID = '5995621997920515361'  # Your Blog ID

@st.cache_resource
def get_google_credentials():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

SYSTEM_INSTRUCTION = """
You are a skilled blog post writer. Follow these guidelines:
1. Use the exact title provided in the title area.
2. Write interesting, relevant content based on the terms in the "about" field.
3. Structure the post with appropriate headings and paragraphs.
4. Images can be little smaller in size to fit on the site, and they should be positioned where the relevant information and images match.
"""

def generate_article(title, about, include_images):
    content_prompt = f"Write a detailed blog post with the title '{title}'. Here's what the content should be about: {about}"
    if include_images:
        content_prompt += " Include image suggestions as described in the system instructions."

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": content_prompt}
        ]
    )
    return response.choices[0].message['content']

def upload_to_blogger(title, content):
    creds = get_google_credentials()
    service = build('blogger', 'v3', credentials=creds)

    posts = service.posts()
    body = {
        "kind": "blogger#post",
        "title": title,
        "content": content
    }

    posts.insert(blogId=BLOG_ID, body=body).execute()

def main():
    st.title("Blog Post Generator and Uploader")

    title = st.text_input("Enter the blog post title:")
    about = st.text_area("Enter what the content should be about:")
    include_images = st.checkbox("Include image suggestions")

    if st.button("Generate Article"):
        if title and about:
            with st.spinner("Generating article..."):
                article_content = generate_article(title, about, include_images)
            
            st.subheader("Generated Article:")
            st.markdown(article_content)

            if st.button("Upload to Blog"):
                with st.spinner("Uploading to Blogger..."):
                    upload_to_blogger(title, article_content)
                st.success("Blog post created successfully!")
        else:
            st.warning("Please enter both a title and content description.")

if __name__ == "__main__":
    main()
