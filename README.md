# Innopolis University LSD Course Project

## How to run LLM time estimation

1. Make sure you have Python 3.10 or later.
2. Install the dependencies (you may create a virtual environment):

    ```bash
    pip install -r requirements.txt
    ```

3. Install Ollama tool [here](https://ollama.com/download).
4. Run these commands in terminal:
    - Gemma 3 12B

        ```bash
        ollama pull gemma3:12b
        python estimate_time.py -i dataset_cropped.csv -o gemma3_12b.csv -m gemma3:12b
        ollama rm gemma3:12b
        ```

    - Llama 3.1 8B

        ```bash
        ollama pull llama3.1:8b
        python estimate_time.py -i dataset_cropped.csv -o llama3-1_8b.csv -m llama3.1:8b
        ollama rm llama3.1:8b
        ```

    - Mistral 7B

        ```bash
        ollama pull mistral:7b
        python estimate_time.py -i dataset_cropped.csv -o mistral_7b.csv -m mistral:7b
        ollama rm mistral:7b
        ```

    - Granite 3.3 8B

        ```bash
        ollama pull granite3.3:8b
        python estimate_time.py -i dataset_cropped.csv -o granite3-3_8b.csv -m granite3.3:8b
        ollama rm granite3.3:8b
        ```
