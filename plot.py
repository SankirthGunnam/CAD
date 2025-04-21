import numpy as np
import matplotlib.pyplot as plt

# Generate sample data
np.random.seed(42)  # For reproducibility
X = np.linspace(0, 10, 50)  # Input feature
y_true = 2 * X + 1  # True relationship: y = 2x + 1
y = y_true + np.random.normal(0, 1, 50)  # Add some noise

# Plot the data points and true relationship
plt.figure(figsize=(12, 5))

# First plot: Data visualization
plt.subplot(1, 2, 1)
plt.scatter(X, y, color="blue", alpha=0.5, label="Data points")
plt.plot(X, y_true, "r--", label="True relationship (y = 2x + 1)")
plt.title("Linear Relationship with Noise")
plt.xlabel("X (Input feature)")
plt.ylabel("y (Target variable)")
plt.legend()
plt.grid(True)

# Second plot: Residuals
residuals = y - y_true
plt.subplot(1, 2, 2)
plt.scatter(X, residuals, color="green", alpha=0.5)
plt.axhline(y=0, color="r", linestyle="--")
plt.title("Residuals (Noise)")
plt.xlabel("X (Input feature)")
plt.ylabel("Residual (y - y_true)")
plt.grid(True)

plt.tight_layout()
plt.show()

# Print some statistical information
print("\nStatistical Information:")
print(f"Mean of residuals: {np.mean(residuals):.4f}")
print(f"Standard deviation of residuals: {np.std(residuals):.4f}")
