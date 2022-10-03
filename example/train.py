import time

def progress(progress, prefix="", width=40):
    xlen = int(progress * width)
    dlen = width - xlen
    print(f"{prefix}[{'=' * xlen}{'.' * dlen}] {progress * 100:.1f}%",
          end='\r', flush=True)

if __name__ == '__main__':
    for i in range(1000):
        time.sleep(0.001)
        progress((i + 1) / 1000, prefix="Training")
    print('')
