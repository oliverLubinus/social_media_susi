# Susi - Social Media Agent

Susi is a modular, extensible social media automation agent. She monitors a OneDrive folder for new images, extracts metadata, generates captions, uploads images to S3, and posts to Instagram (and soon other platforms) using a unified workflow. Susi is designed for easy extension to new use cases and platforms.

## Features
- Monitors a OneDrive folder for new images
- Extracts image metadata (title, comments, etc.)
- Generates captions using templates or generative AI (extensible)
- Uploads images to AWS S3 for public hosting
- Posts to Instagram (modular, easily extendable to LinkedIn, etc.)
- Sends email notifications for errors and successful posts
- Robust logging and error handling with retries
- Runs on a schedule or in polling mode (Docker-ready)

## Setup
1. **Clone the repository**
2. **Install dependencies**
	 ```sh
	 pip install -r requirements.txt
	 ```
3. **Configure secrets**
	 - Copy `.env.example` to `.env` and fill in your secrets (AWS, Instagram, email, etc.)
	 - Add `.env` to `.gitignore` to keep secrets safe
4. **Edit `config.yaml`**
	 - Reference secrets using `${VAR}` syntax (e.g., `${AWS_ACCESS_KEY_ID}`)
	 - Adjust OneDrive, S3, and email settings as needed
5. **Set up OneDrive and Instagram API access**
	 - Follow the instructions in the docs or comments to register your app and obtain tokens

## Usage

### Local Run
```sh
python -m susi.main
```

### Docker
Build and run the container:
```sh
docker build -t susi .
docker run --env-file .env susi
```

### Configuration
- All settings are in `config.yaml` (secrets referenced from `.env`)
- Logging output is written to the file specified in `config.yaml`
- You can choose polling or schedule mode in the `main()` function

## Extending Susi
- To add a new social platform, implement a new class in `susi/social_posters/` inheriting from `SocialPoster`.
- To use generative AI for captions, swap out or extend the caption generation step in `main.py`.
- The workflow is modular—each step can be replaced or extended as needed.

## Troubleshooting

- **No posts are being made:**
	- Check the logs in the file specified in `config.yaml` for errors.
	- Ensure your `.env` file is present and all required secrets are set.
	- Verify OneDrive and Instagram API credentials are valid and not expired.

- **Email notifications not sent:**
	- Check SMTP or Gmail API credentials in `.env` and `config.yaml`.
	- Look for error logs related to email sending.

- **S3 upload fails:**
	- Ensure your AWS credentials are correct and have the right permissions.
	- Check the S3 bucket name and region.

- **Instagram post fails:**
	- Make sure the image URL is public and accessible.
	- Check that your Instagram access token is valid and has the required permissions.

- **Environment variables not loaded:**
	- Make sure you are running the app from the project root and `.env` exists.
	- Use `print(os.environ)` in `main.py` to debug environment loading.

## OneDrive Authentication: Creating and Using token_result.json

To enable Susi to access OneDrive, you must authenticate and generate a token file:

1. **Run the OAuth flow locally:**
   - Run the onedrive_auth.py file on your local machine (not in Docker) and follow the prompts to log in to your Microsoft account or copy&paste the token from the browser url (everything between code= and &session) into the terminal where you ran the script.
   - The authentication process will generate `token_result.json` and `token_cache.bin` in your project directory.

2. **Copy the token files:**
   - Place `token_result.json` and `token_cache.bin` in the root of your project (next to your Dockerfile).

3. **Build and run the Docker container:**
   - The Dockerfile is set up to copy these files into the container so Susi can use the access token for OneDrive API calls.

**Note:** If your token expires or is revoked, repeat the OAuth flow to generate new token files.

## Contributing
Pull requests and feature suggestions are welcome! Please open an issue or PR.

---
For more details, see the code docstrings and comments throughout the project.
