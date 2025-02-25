import numpy as np
import matplotlib.pyplot as plt
print(bytes.fromhex("486170707920456e67696e6565727320646179").decode())
x = np.linspace(-2, 2, 100000)
plt.fill_between(x, (1 - (np.abs(x) - 1)**2)**0.5, -3 * (1 - (np.abs(x) / 2)**0.5)**0.5, color='r')
plt.text(0, -0.5, "Engineers", fontsize=24, color='w', ha='center')
plt.axis('off')
plt.show()