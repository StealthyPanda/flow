# Flow toolkit
---

A simple development toolkit for streamlining ML and DL workflows.

## Getting started

### Installation

The base compiler can be installed via `pip`:
```bash
pip install flow-toolkit
```

Next, install a plugin for your intended output. For example:

```bash
flow -i https://github.com/StealthyPanda/pytorch-backend.git
```


Any github repository can be used as a valid flow plugin, as long as it contains a `plugin.py` in its root directory, and contains a `main` function.


### Quick Start

A simple flow for a dense neural network would be:

```
// example.fl

flow linear(x) [weights, biases] {
    return
        (weights @ x) + biases;
}

flow NeuralNetwork (x) {
    let linear l1;
    let linear l2;

    y = l1(x);
    y = l2(y);

    return y;
}

build NeuralNetwork simple {
    x => 784;
    output => 10;
}
```

Build the flow to a pytorch model with:
```bash
flow -f example.fl -o example
```




