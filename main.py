"""
LinkedIn Bot - Automate LinkedIn interactions
Supports creating posts (text, URL, image/video), reacting, and commenting
"""

import requests
import json
from typing import Optional, List, Dict, Any
from pathlib import Path


class LinkedInBot:
    """
    LinkedIn Bot for automating LinkedIn interactions via API
    """
    
    BASE_URL = "https://api.linkedin.com/v2"
    HEADERS = {
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }
    
    def __init__(self, access_token: str):
        """
        Initialize the LinkedIn Bot with an access token
        
        Args:
            access_token: OAuth 2.0 access token with w_member_social scope
        """
        self.access_token = access_token
        self.headers = self.HEADERS.copy()
        self.headers["Authorization"] = f"Bearer {access_token}"
        self.person_urn = None
    
    def get_user_info(self) -> Dict[str, Any]:
        """
        Get the authenticated user's profile information
        
        Returns:
            Dictionary containing user profile data including person URN
        """
        url = f"{self.BASE_URL}/userinfo"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            data = response.json()
            # Extract person URN from the response
            self.person_urn = f"urn:li:person:{data['sub']}"
            return data
        else:
            raise Exception(f"Failed to get user info: {response.status_code} - {response.text}")
    
    def create_text_post(self, text: str, visibility: str = "PUBLIC") -> str:
        """
        Create a simple text post on LinkedIn
        
        Args:
            text: The text content of the post
            visibility: Either "PUBLIC" or "CONNECTIONS" (default: PUBLIC)
        
        Returns:
            The URN of the created post
        """
        if not self.person_urn:
            self.get_user_info()
        
        url = f"{self.BASE_URL}/ugcPosts"
        
        payload = {
            "author": self.person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code == 201:
            post_id = response.headers.get('X-RestLi-Id')
            print(f"✅ Text post created successfully! Post ID: {post_id}")
            return post_id
        else:
            raise Exception(f"Failed to create text post: {response.status_code} - {response.text}")
    
    def create_url_post(
        self, 
        text: str, 
        url: str, 
        title: Optional[str] = None, 
        description: Optional[str] = None,
        visibility: str = "PUBLIC"
    ) -> str:
        """
        Create a post with a URL/article link
        
        Args:
            text: The commentary text for the post
            url: The URL to share
            title: Optional title for the URL preview
            description: Optional description for the URL preview
            visibility: Either "PUBLIC" or "CONNECTIONS" (default: PUBLIC)
        
        Returns:
            The URN of the created post
        """
        if not self.person_urn:
            self.get_user_info()
        
        api_url = f"{self.BASE_URL}/ugcPosts"
        
        media_item = {
            "status": "READY",
            "originalUrl": url
        }
        
        if title:
            media_item["title"] = {"text": title}
        if description:
            media_item["description"] = {"text": description}
        
        payload = {
            "author": self.person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "ARTICLE",
                    "media": [media_item]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }
        
        response = requests.post(api_url, headers=self.headers, json=payload)
        
        if response.status_code == 201:
            post_id = response.headers.get('X-RestLi-Id')
            print(f"✅ URL post created successfully! Post ID: {post_id}")
            return post_id
        else:
            raise Exception(f"Failed to create URL post: {response.status_code} - {response.text}")
    
    def register_image_upload(self) -> Dict[str, str]:
        """
        Register an image upload and get the upload URL
        
        Returns:
            Dictionary containing 'uploadUrl' and 'asset' URN
        """
        if not self.person_urn:
            self.get_user_info()
        
        url = f"{self.BASE_URL}/assets?action=registerUpload"
        
        payload = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": self.person_urn,
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent"
                    }
                ]
            }
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            upload_url = data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
            asset = data['value']['asset']
            return {"uploadUrl": upload_url, "asset": asset}
        else:
            raise Exception(f"Failed to register image upload: {response.status_code} - {response.text}")
    
    def register_video_upload(self) -> Dict[str, str]:
        """
        Register a video upload and get the upload URL
        
        Returns:
            Dictionary containing 'uploadUrl' and 'asset' URN
        """
        if not self.person_urn:
            self.get_user_info()
        
        url = f"{self.BASE_URL}/assets?action=registerUpload"
        
        payload = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-video"],
                "owner": self.person_urn,
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent"
                    }
                ]
            }
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            upload_url = data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
            asset = data['value']['asset']
            return {"uploadUrl": upload_url, "asset": asset}
        else:
            raise Exception(f"Failed to register video upload: {response.status_code} - {response.text}")
    
    def upload_media_file(self, file_path: str, upload_url: str) -> bool:
        """
        Upload an image or video file to LinkedIn
        
        Args:
            file_path: Path to the image or video file
            upload_url: The upload URL obtained from register_image_upload or register_video_upload
        
        Returns:
            True if upload was successful
        """
        with open(file_path, 'rb') as file:
            file_data = file.read()
        
        upload_headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        response = requests.post(upload_url, headers=upload_headers, data=file_data)
        
        if response.status_code == 201:
            print(f"✅ Media file uploaded successfully!")
            return True
        else:
            raise Exception(f"Failed to upload media file: {response.status_code} - {response.text}")
    
    def create_image_post(
        self,
        text: str,
        image_path: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        visibility: str = "PUBLIC"
    ) -> str:
        """
        Create a post with an image
        
        Args:
            text: The commentary text for the post
            image_path: Path to the image file
            title: Optional title for the image
            description: Optional description for the image
            visibility: Either "PUBLIC" or "CONNECTIONS" (default: PUBLIC)
        
        Returns:
            The URN of the created post
        """
        # Step 1: Register the upload
        print("📝 Registering image upload...")
        upload_info = self.register_image_upload()
        
        # Step 2: Upload the image
        print(f"📤 Uploading image from {image_path}...")
        self.upload_media_file(image_path, upload_info['uploadUrl'])
        
        # Step 3: Create the post
        print("📮 Creating image post...")
        url = f"{self.BASE_URL}/ugcPosts"
        
        media_item = {
            "status": "READY",
            "media": upload_info['asset']
        }
        
        if title:
            media_item["title"] = {"text": title}
        if description:
            media_item["description"] = {"text": description}
        
        payload = {
            "author": self.person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "IMAGE",
                    "media": [media_item]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code == 201:
            post_id = response.headers.get('X-RestLi-Id')
            print(f"✅ Image post created successfully! Post ID: {post_id}")
            return post_id
        else:
            raise Exception(f"Failed to create image post: {response.status_code} - {response.text}")
    
    def create_video_post(
        self,
        text: str,
        video_path: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        visibility: str = "PUBLIC"
    ) -> str:
        """
        Create a post with a video
        
        Args:
            text: The commentary text for the post
            video_path: Path to the video file
            title: Optional title for the video
            description: Optional description for the video
            visibility: Either "PUBLIC" or "CONNECTIONS" (default: PUBLIC)
        
        Returns:
            The URN of the created post
        """
        # Step 1: Register the upload
        print("📝 Registering video upload...")
        upload_info = self.register_video_upload()
        
        # Step 2: Upload the video
        print(f"📤 Uploading video from {video_path}...")
        self.upload_media_file(video_path, upload_info['uploadUrl'])
        
        # Step 3: Create the post
        print("📮 Creating video post...")
        url = f"{self.BASE_URL}/ugcPosts"
        
        media_item = {
            "status": "READY",
            "media": upload_info['asset']
        }
        
        if title:
            media_item["title"] = {"text": title}
        if description:
            media_item["description"] = {"text": description}
        
        payload = {
            "author": self.person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "VIDEO",
                    "media": [media_item]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code == 201:
            post_id = response.headers.get('X-RestLi-Id')
            print(f"✅ Video post created successfully! Post ID: {post_id}")
            return post_id
        else:
            raise Exception(f"Failed to create video post: {response.status_code} - {response.text}")
    
    def like_post(self, post_urn: str) -> bool:
        """
        Like a LinkedIn post
        
        Args:
            post_urn: The URN of the post to like (e.g., "urn:li:share:123456789")
        
        Returns:
            True if successful
        """
        if not self.person_urn:
            self.get_user_info()
        
        url = f"{self.BASE_URL}/socialActions/{post_urn}/likes"
        
        payload = {
            "actor": self.person_urn
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code in [200, 201]:
            print(f"👍 Successfully liked post: {post_urn}")
            return True
        else:
            raise Exception(f"Failed to like post: {response.status_code} - {response.text}")
    
    def react_to_post(self, post_urn: str, reaction_type: str = "LIKE") -> bool:
        """
        React to a LinkedIn post with different reaction types
        
        Args:
            post_urn: The URN of the post to react to
            reaction_type: Type of reaction - LIKE, PRAISE, APPRECIATION, EMPATHY, INTEREST, ENTERTAINMENT
        
        Returns:
            True if successful
        """
        if not self.person_urn:
            self.get_user_info()
        
        # Valid reaction types
        valid_reactions = ["LIKE", "PRAISE", "APPRECIATION", "EMPATHY", "INTEREST", "ENTERTAINMENT"]
        
        if reaction_type.upper() not in valid_reactions:
            raise ValueError(f"Invalid reaction type. Must be one of: {', '.join(valid_reactions)}")
        
        url = f"{self.BASE_URL}/socialActions/{post_urn}/reactions"
        
        payload = {
            "actor": self.person_urn,
            "reactionType": reaction_type.upper()
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code in [200, 201]:
            emoji_map = {
                "LIKE": "👍",
                "PRAISE": "🙌",
                "APPRECIATION": "❤️",
                "EMPATHY": "🤗",
                "INTEREST": "💡",
                "ENTERTAINMENT": "😂"
            }
            emoji = emoji_map.get(reaction_type.upper(), "👍")
            print(f"{emoji} Successfully reacted to post with {reaction_type}: {post_urn}")
            return True
        else:
            raise Exception(f"Failed to react to post: {response.status_code} - {response.text}")
    
    def comment_on_post(self, post_urn: str, comment_text: str) -> str:
        """
        Comment on a LinkedIn post
        
        Args:
            post_urn: The URN of the post to comment on
            comment_text: The text of the comment
        
        Returns:
            The URN of the created comment
        """
        if not self.person_urn:
            self.get_user_info()
        
        url = f"{self.BASE_URL}/socialActions/{post_urn}/comments"
        
        payload = {
            "actor": self.person_urn,
            "message": {
                "text": comment_text
            }
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code in [200, 201]:
            comment_id = response.headers.get('X-RestLi-Id', 'Unknown')
            print(f"💬 Successfully commented on post: {post_urn}")
            print(f"   Comment ID: {comment_id}")
            return comment_id
        else:
            raise Exception(f"Failed to comment on post: {response.status_code} - {response.text}")
    
    def delete_post(self, post_urn: str) -> bool:
        """
        Delete a LinkedIn post
        
        Args:
            post_urn: The URN of the post to delete (e.g., "urn:li:ugcPost:123456789" or just "123456789")
        
        Returns:
            True if successful
        """
        # Extract just the ID if a full URN is provided
        if post_urn.startswith("urn:li:ugcPost:"):
            post_id = post_urn.replace("urn:li:ugcPost:", "")
        elif post_urn.startswith("urn:li:share:"):
            post_id = post_urn.replace("urn:li:share:", "")
        else:
            post_id = post_urn
        
        # URL encode the URN properly
        url = f"{self.BASE_URL}/ugcPosts/urn%3Ali%3AugcPost%3A{post_id}"
        
        response = requests.delete(url, headers=self.headers)
        
        if response.status_code == 204:
            print(f"🗑️ Successfully deleted post: {post_urn}")
            return True
        else:
            raise Exception(f"Failed to delete post: {response.status_code} - {response.text}")
    
    
# Example usage
if __name__ == "__main__":
    # Replace with your actual access token
    ACCESS_TOKEN = "AQWOjSA6I45_cSlZN6QE6f6KiasGx_xdz9QvecX1JJXttbNV_rTsmO91ZNYTyG3bd0qbsYhXDNR8muV8QZyyfssUBP7eE-3OKPvJ8fHgEjxrD6ToPQK8KsXfzNfmvbklmQm07uI_Y4JcQCli16j2MknGXszRmXOx31N277nJsHxnBV9ZPki6PgtM79mW2AYDtbZel1AmTpRo_pf48kz0p_vVyYR26KQ3Mg_M9FwrEHpHXO7Vw7Pwinu7XFS39SpK97wuxGoAWaGHHbx0JLawlF4jgSvj5Zcmo2NafNKblewnbi1VXVXkV45d3w9xWhPhwmgg_JwhSNDdpipN2clkAjSeV6k42g"
    
    # Initialize the bot
    bot = LinkedInBot(ACCESS_TOKEN)
    
    # Get user info (this also sets the person_urn)
    try:
        user_info = bot.get_user_info()
        print(f"✅ Authenticated as: {user_info.get('name')} {user_info.get('email')}")
        print(f"   Person URN: {bot.person_urn}\n")
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
    
    # Example 1: Create a simple text post
    try:
        print("=" * 50)
        print("Example 1: Creating a text post")
        print("=" * 50)
        post_id = bot.create_text_post(
            text="Hello LinkedIn! 🚀 Excited to share my journey in automation and AI!",
            visibility="PUBLIC"
        )
        print()
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # Example 2: Create a URL post
    try:
        print("=" * 50)
        print("Example 2: Creating a URL post")
        print("=" * 50)
        post_id = bot.create_url_post(
            text="Great insights on the future of AI! 🤖 #AI #Technology",
            url="https://blog.linkedin.com/",
            title="Official LinkedIn Blog",
            description="Your source for insights and information about LinkedIn.",
            visibility="PUBLIC"
        )
        print()
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # Example 3: Create an image post
    # Uncomment and provide an actual image path to test
    # try:
    #     print("=" * 50)
    #     print("Example 3: Creating an image post")
    #     print("=" * 50)
    #     post_id = bot.create_image_post(
    #         text="Check out this amazing view! with API 🌄 #Photography",
    #         image_path="generated_image.png",
    #         title="Beautiful Landscape API",
    #         description="Captured during my morning hike with API",
    #         visibility="PUBLIC"
    #     )
    #     print()
    # except Exception as e:
    #     print(f"❌ Error: {e}\n")
    
    # Example 4: React to a post
    # Replace with an actual post URN
    # try:
    #     print("=" * 50)
    #     print("Example 4: Reacting to a post")
    #     print("=" * 50)
    #     bot.react_to_post(
    #         post_urn="urn:li:share:1234567890",
    #         reaction_type="PRAISE"
    #     )
    #     print()
    # except Exception as e:
    #     print(f"❌ Error: {e}\n")
    
    # Example 5: Comment on a post
    # Replace with an actual post URN
    # try:
    #     print("=" * 50)
    #     print("Example 5: Commenting on a post")
    #     print("=" * 50)
    #     bot.comment_on_post(
    #         post_urn="urn:li:share:1234567890",
    #         comment_text="Great post! Thanks for sharing this valuable insight. 💡"
    #     )
    #     print()
    # except Exception as e:
    #     print(f"❌ Error: {e}\n")

    # Example 6: Delete a post
    # Replace with an actual post URN
    try:
        print("=" * 50)
        print("Example 6: Deleting a post")
        print("=" * 50)
        bot.delete_post(post_urn="urn:li:ugcPost:7415488103701917696")
        print()
    except Exception as e:
        print(f"❌ Error: {e}\n")

    # Example 7: Upload a video post
    # try:
    #     print("=" * 50)
    #     print("Example 7: Uploading a video post")
    #     print("=" * 50)
    #     bot.create_video_post(
    #         text="My latest video tutorial! with API 🎥 #Tutorial",
    #         video_path="Video-310.mp4",
    #         title="How to Build a LinkedIn Bot",
    
    #         description="Step-by-step guide",
    #         visibility="PUBLIC"
    #     )
    #     print()
    # except Exception as e:
    #     print(f"❌ Error: {e}\n")

    print("=" * 50)
    print("✅ All examples completed!")
    print("=" * 50)
