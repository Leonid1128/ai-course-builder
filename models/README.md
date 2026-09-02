GGUF models go here. They are not committed.

Example:

    llama-server -m model.gguf -ngl 99 -c 16384 --host 0.0.0.0 --port 11434 --embeddings --pooling mean
