from typing import NewType, Generator, Iterator


ImageGenerator = NewType("ImageGenerator", Generator[tuple[list[str], str], int, tuple[list[str], str]])
SentenceGenerator = NewType("SentenceGenerator", Iterator[tuple[list, str]])
