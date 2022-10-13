Python 3.7

Ядро для ipykernel

```python -m ipykernel install --user --name pa --display-name "Python 3.7 (pa)"```

Стабильная версия PyTorch 1.10.0 с CUDA для 30 серии Nvidia

```pip install torch==1.10.0+cu113 torchvision==0.11.0+cu113 -f https://download.pytorch.org/whl/torch_stable.html```

---

* **train/train.sh** - скрипт обучения, для запуска настроить пути в скрипте и в конфиге
* **config/train.conf** - конфиг обучения
* **Pronouns.py** - инструменты для создания набора даннных для обучения и тестирования

---
Структура проекта
```
pronouns_analysis
├── config
├── data
├── eval
├── generator
├── logs
├── rdf
├── train
├── trained_models
├── true_keys
└── Pronouns.py
```