from picamera import PiCamera
from os.path import isfile

# Output image resolution.
IMAGE_RES = (640, 480)
JPG_QUALITY = 10
IMAGE_FORMAT = "jpeg"
BW_IMAGE = False
VERT_FLIP = True

TAKEN_FILE = "taken_pics.txt"
SENT_FILE = "sent_pics.txt"


def take_pic():
    """Captures an image from the camera and remembers it as taken but not yet sent"""
    file_path = get_next_image_name()
    try:
        camera = PiCamera(resolution=IMAGE_RES)
        if (BW_IMAGE):
            camera.color_effects = (128, 128)
        camera.vflip = VERT_FLIP
        camera.capture(file_path, format=IMAGE_FORMAT, quality=JPG_QUALITY)
    finally:
        camera.close()

    print("Picture captured")
    with open(TAKEN_FILE, "a+") as f:
        f.write(file_path + '\n')


def get_unsent_pics():
    """Gets all taken camera image which have not yet been sent"""
    # Need to create files if they do not already exist
    open(SENT_FILE, "a").close()
    open(TAKEN_FILE, "a").close()

    unsent = []
    with open(TAKEN_FILE, "r") as taken:
        with open(SENT_FILE, "r") as sent:
            for line in taken:
                image = line.strip()
                if image not in sent and isfile(image):
                    unsent.append(image)
    return unsent


def mark_pics_sent(file_paths) -> None:
    """Mark one or more camera images as sent"""
    with open(SENT_FILE, "a+") as sent_file:
        if (isinstance(file_paths, str)):
            if not file_paths[-1] == '\n':
                file_paths += '\n'
            sent_file.write(file_paths)
        else:
            paths_with_line_ends = []
            for fp in file_paths:
                paths_with_line_ends.append(fp if fp[-1] == '\n' else fp + '\n')
            sent_file.writelines(paths_with_line_ends)


def get_next_image_name():
    """Get file name to save next image as"""
    try:
        with open(TAKEN_FILE, 'r') as f:
            lines = f.readlines()
            if lines:
                last_image = lines[-1]
                ending_index = last_image.find(f".{IMAGE_FORMAT}")
                return "{}.{}".format(
                    int(last_image[:ending_index]) + 1,
                    IMAGE_FORMAT
                )
            else:
                return f"1.{IMAGE_FORMAT}"
    except FileNotFoundError:
        return f"1.{IMAGE_FORMAT}"


if __name__ == '__main__':
    take_pic()
