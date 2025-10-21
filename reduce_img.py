import os
from PIL import Image

def compress_and_convert_recursive_v1(input_folder, output_folder, quality=85):
    """
    Recursively convert and resize images while mirroring the folder structure.
    Keeps aspect ratio and converts everything to JPG.

    Parameters:
        input_folder (str): Root folder containing images (can have subfolders)
        output_folder (str): Destination root folder for converted images
        quality (int): JPEG quality (1–100)
    """
    for root, _, files in os.walk(input_folder):
        # Compute the corresponding subfolder path in output
        relative_path = os.path.relpath(root, input_folder)
        dest_dir = os.path.join(output_folder, relative_path)
        os.makedirs(dest_dir, exist_ok=True)

        for filename in files:
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                input_path = os.path.join(root, filename)
                output_name = os.path.splitext(filename)[0] + ".jpg"
                output_path = os.path.join(dest_dir, output_name)

                try:
                    with Image.open(input_path) as img:
                        # Convert PNGs with transparency to RGB
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")

                        width, height = img.size
                        # Dynamic resizing depending on image size
                        if max(width, height) > 3000:
                            scale = 0.5
                        elif max(width, height) > 1500:
                            scale = 0.75
                        else:
                            scale = 1.0

                        if scale < 1.0:
                            new_size = (int(width * scale), int(height * scale))
                            img = img.resize(new_size, Image.Resampling.LANCZOS)

                        img.save(output_path, "JPEG", quality=quality, optimize=True)
                        print(f"✅ {input_path} → {output_path} ({width}x{height} → {img.size[0]}x{img.size[1]})")

                except Exception as e:
                    print(f"❌ Error processing {input_path}: {e}")

def compress_and_convert_recursive(input_folder, output_folder, quality=85, max_size=3000):
    """
    Recursively convert and resize images while mirroring the folder structure.
    Keeps aspect ratio and converts everything to JPG.

    Parameters:
        input_folder (str): Root folder containing images (can have subfolders)
        output_folder (str): Destination root folder for converted images
        quality (int): JPEG quality (1–100)
        max_size (int): Maximum width or height in pixels (preserves aspect ratio)
    """
    for root, _, files in os.walk(input_folder):
        # Compute the corresponding subfolder path in output
        relative_path = os.path.relpath(root, input_folder)
        dest_dir = os.path.join(output_folder, relative_path)
        os.makedirs(dest_dir, exist_ok=True)

        for filename in files:
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                input_path = os.path.join(root, filename)
                output_name = os.path.splitext(filename)[0] + ".jpg"
                output_path = os.path.join(dest_dir, output_name)

                try:
                    with Image.open(input_path) as img:
                        # Convert PNGs with transparency to RGB
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")

                        width, height = img.size

                        # Determine scale factor to fit within max_size
                        if width > max_size or height > max_size:
                            ratio = min(max_size / width, max_size / height)
                            new_size = (int(width * ratio), int(height * ratio))
                            img = img.resize(new_size, Image.Resampling.LANCZOS)
                        else:
                            new_size = (width, height)

                        img.save(output_path, "JPEG", quality=quality, optimize=True)
                        print(f"✅ {input_path} → {output_path} ({width}x{height} → {new_size[0]}x{new_size[1]})")

                except Exception as e:
                    print(f"❌ Error processing {input_path}: {e}")

# Example usage
if __name__ == "__main__":
    input_folder = "./P2_filtrades"
    output_folder = "p2_recompressed_photos"
    compress_and_convert_recursive(input_folder, output_folder, quality=85)
