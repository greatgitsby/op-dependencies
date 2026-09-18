extern "C" int check_agnos();
extern "C" int check_camera_kt();

int main() {
  return check_agnos() || check_camera_kt();
}
