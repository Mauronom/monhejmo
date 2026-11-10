import os
from domain import Moviment, FontMoviments


class RepositoriMovimentsNorma43(FontMoviments):
    """
    Font de moviments que llegeix fitxers Norma 43 (.n43) utilitzant norma43parser.
    Cada fitxer correspon a un banc, que pren el nom del fitxer.
    """

    def __init__(self):
        from norma43parser import Norma43Parser, DateFormat
        self._parser = Norma43Parser(DateFormat.ENGLISH)  # Utilitza AAAAMMDD

    def llegir(self, directori):
        moviments = []
        for fitxer in os.listdir(directori):
            if fitxer.lower().endswith(".n43"):
                banc = os.path.splitext(fitxer)[0]
                path = os.path.join(directori, fitxer)
                with open(path, "r", encoding="latin-1", errors="ignore") as f:
                    contents = f.read()
                doc = self._parser.parse(contents)
                for account in doc.accounts:
                    for line in account.movement_lines:
                        moviments.append(
                            Moviment(
                                line.transaction_date,
                                line.extra_information[0].replace('      ', ' ').strip(),
                                line.amount,
                                line.balance,
                                banc
                            )
                        )
        return sorted(moviments, key=lambda m: m.data)
