import matplotlib.pyplot as plt
import config
import os

def save_chart(fig, filename):
    file_path = os.path.join(config.CHARTS_DIR, filename)
    fig.savefig(file_path)
    plt.close(fig)
    print(f"图表已保存到 {file_path}")