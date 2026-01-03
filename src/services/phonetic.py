"""Phonetic search module optimized for Indian names.

Handles common transliteration variants in Hindi/Indian names:
- Ram, Raam, Rama → same phonetic code
- Shailesh, Shylesh, Shailash → same phonetic code
- Vijay, Wijay → same phonetic code
"""

import re
from typing import List, Tuple, Optional


class IndianPhoneticSearch:
    """Phonetic matching optimized for Indian names."""

    # Indian phonetic equivalences (Hindi transliteration variants)
    EQUIVALENCES = [
        # Vowel variations (most common in Indian names)
        ('aa', 'a'),    # Raam → Ram
        ('ee', 'i'),    # Pradeep → Pradip
        ('ii', 'i'),    # Sriinivas → Srinivas
        ('oo', 'u'),    # Sooraj → Suraj
        ('uu', 'u'),    # Ruupa → Rupa
        ('ou', 'u'),    # Sourav → Surav
        ('ai', 'e'),    # Sainath → Senath
        ('au', 'o'),    # Gaurav → Gorav
        ('ey', 'i'),    # Pandey → Pandi
        ('ay', 'e'),    # Uday → Ude
        ('iya', 'ia'),  # Saniya → Sania
        ('ea', 'ia'),   # Shea → Shia

        # Aspirated consonants (Hindi special - very common)
        ('bh', 'b'),    # Bharat → Barat
        ('ch', 'c'),    # Chandra → Candra
        ('dh', 'd'),    # Dhiraj → Diraj
        ('gh', 'g'),    # Ghosh → Gosh
        ('jh', 'j'),    # Jharna → Jarna
        ('kh', 'k'),    # Khan → Kan
        ('ph', 'f'),    # Phadke → Fadke
        ('th', 't'),    # Thakur → Takur

        # Sibilant variations
        ('sh', 's'),    # Shyam → Syam
        ('sch', 's'),   # Kirsch → Kirs
        ('shh', 's'),   # Extra h

        # Common confusions
        ('v', 'w'),     # Vijay → Wijay (Bengali/regional)
        ('w', 'v'),     # Reverse mapping
        ('z', 'j'),     # Zarina → Jarina
        ('q', 'k'),     # Qureshi → Kureshi
        ('x', 'ks'),    # Xavier → Ksavier

        # Retroflex variations (t/d variations in South Indian names)
        ('tt', 't'),    # Mutt → Mut
        ('dd', 'd'),    # Reddy → Redy

        # Nasal variations
        ('ng', 'n'),    # Singh → Sin (at end)
        ('nd', 'n'),    # Sometimes simplified

        # Terminal variations
        ('ey', 'i'),    # Pandey → Pandi
        ('ie', 'i'),    # Swamie → Swami
        ('y', 'i'),     # Terminal y → i
    ]

    # Vowels to remove (except first)
    VOWELS = set('aeiou')

    # Common Indian name suffixes that can be normalized
    SUFFIXES = [
        ('kumar', 'kmr'),
        ('singh', 'sng'),
        ('sharma', 'srm'),
        ('gupta', 'gpt'),
        ('verma', 'vrm'),
        ('pandey', 'pnd'),
        ('mishra', 'msr'),
        ('choudhary', 'chd'),
        ('yadav', 'ydv'),
        ('reddy', 'rdy'),
        ('naidu', 'ndu'),
        ('iyer', 'ir'),
        ('iyengar', 'ingr'),
    ]

    def __init__(self):
        """Initialize the phonetic search."""
        # Pre-compile suffix patterns for efficiency
        self._suffix_pattern = re.compile(
            r'\b(' + '|'.join(s[0] for s in self.SUFFIXES) + r')\b',
            re.IGNORECASE
        )

    def get_phonetic_code(self, name: str) -> str:
        """
        Generate phonetic code for an Indian name.

        Args:
            name: The name to encode

        Returns:
            A normalized phonetic code for comparison
        """
        if not name:
            return ""

        # Normalize: lowercase and strip
        name = name.lower().strip()

        # Remove non-alphabetic characters except spaces
        name = re.sub(r'[^a-z\s]', '', name)

        # Apply equivalences
        for long_form, short_form in self.EQUIVALENCES:
            name = name.replace(long_form, short_form)

        # Remove double letters
        result = []
        prev = ''
        for char in name:
            if char != prev or char == ' ':
                result.append(char)
            prev = char
        name = ''.join(result)

        # Remove vowels except first letter of each word
        words = name.split()
        encoded_words = []
        for word in words:
            if len(word) > 1:
                first = word[0]
                rest = ''.join(c for c in word[1:] if c not in self.VOWELS)
                encoded_words.append(first + rest)
            elif word:
                encoded_words.append(word)

        return ' '.join(encoded_words).upper()

    def get_phonetic_code_aggressive(self, name: str) -> str:
        """
        Generate a more aggressive phonetic code for fuzzy matching.
        Removes all vowels and spaces.

        Args:
            name: The name to encode

        Returns:
            A highly normalized code for loose matching
        """
        code = self.get_phonetic_code(name)
        # Remove all vowels and spaces for very loose matching
        return ''.join(c for c in code if c not in self.VOWELS and c != ' ')

    def match_score(self, query: str, candidate: str) -> float:
        """
        Calculate phonetic similarity score between query and candidate.

        Args:
            query: The search query
            candidate: The candidate name to match against

        Returns:
            Float between 0.0 (no match) and 1.0 (perfect match)
        """
        if not query or not candidate:
            return 0.0

        q_code = self.get_phonetic_code(query)
        c_code = self.get_phonetic_code(candidate)

        # Exact phonetic match
        if q_code == c_code:
            return 1.0

        # One contains the other
        if q_code in c_code:
            return 0.9
        if c_code in q_code:
            return 0.85

        # Prefix match (searching "Ram" matches "Ramesh")
        q_words = q_code.split()
        c_words = c_code.split()

        if q_words and c_words:
            # First word prefix match
            if c_words[0].startswith(q_words[0]):
                return 0.8

            # Any word prefix match
            for q_word in q_words:
                for c_word in c_words:
                    if c_word.startswith(q_word):
                        return 0.75

        # Calculate edit distance similarity
        distance = self._levenshtein(q_code.replace(' ', ''), c_code.replace(' ', ''))
        max_len = max(len(q_code.replace(' ', '')), len(c_code.replace(' ', '')))

        if max_len == 0:
            return 0.0

        similarity = 1 - (distance / max_len)
        return max(0, similarity * 0.7)  # Scale down edit-distance matches

    def _levenshtein(self, s1: str, s2: str) -> int:
        """
        Calculate Levenshtein edit distance between two strings.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Integer edit distance
        """
        if len(s1) < len(s2):
            return self._levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)

        prev_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                # Cost is 0 if characters match, 1 otherwise
                insertions = prev_row[j + 1] + 1
                deletions = curr_row[j] + 1
                substitutions = prev_row[j] + (c1 != c2)
                curr_row.append(min(insertions, deletions, substitutions))
            prev_row = curr_row

        return prev_row[-1]

    def search(
        self,
        query: str,
        candidates: List[Tuple[int, str]],
        threshold: float = 0.6
    ) -> List[Tuple[int, str, float]]:
        """
        Search for matching names from a list of candidates.

        Args:
            query: The search query
            candidates: List of (id, name) tuples to search
            threshold: Minimum match score to include (0.0 to 1.0)

        Returns:
            List of (id, name, score) tuples, sorted by score descending
        """
        results = []

        for id_, name in candidates:
            score = self.match_score(query, name)
            if score >= threshold:
                results.append((id_, name, score))

        # Sort by score descending
        results.sort(key=lambda x: -x[2])
        return results


class MultiStrategySearch:
    """
    Combines multiple search strategies for best results:
    1. Exact match
    2. LIKE/prefix match
    3. Phonetic match
    4. FTS5 match
    """

    def __init__(self, db_service):
        """
        Initialize with a database service.

        Args:
            db_service: The DatabaseService instance
        """
        self.db = db_service
        self.phonetic = IndianPhoneticSearch()

    def search_patients(
        self,
        query: str,
        limit: int = 20
    ) -> List[Tuple]:
        """
        Search patients using multiple strategies.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of (patient, score, match_type) tuples
        """
        if not query or not query.strip():
            return []

        query = query.strip()
        results = {}  # patient_id -> (patient, score, match_type)

        # 1. Exact UHID match (highest priority)
        if query.upper().startswith('EMR-') or query.isdigit():
            exact = self._search_uhid(query)
            for patient in exact:
                results[patient.id] = (patient, 1.0, 'uhid_exact')

        # 2. Basic LIKE search on name
        like_results = self.db.search_patients_basic(query)
        for patient in like_results:
            if patient.id not in results:
                # Check if it's an exact or prefix match
                name_lower = patient.name.lower()
                query_lower = query.lower()
                if name_lower == query_lower:
                    results[patient.id] = (patient, 0.98, 'name_exact')
                elif name_lower.startswith(query_lower):
                    results[patient.id] = (patient, 0.95, 'name_prefix')
                else:
                    results[patient.id] = (patient, 0.85, 'name_like')

        # 3. FTS5 search
        try:
            fts_results = self.db.fts_search_patients(query, limit=limit)
            for patient in fts_results:
                if patient.id not in results:
                    results[patient.id] = (patient, 0.8, 'fts')
        except Exception:
            pass  # FTS might not be available

        # 4. Phonetic search (for remaining slots)
        if len(results) < limit:
            all_patients = self.db.get_all_patients()
            candidates = [(p.id, p.name) for p in all_patients if p.id not in results]
            phonetic_matches = self.phonetic.search(query, candidates, threshold=0.6)

            for id_, name, score in phonetic_matches:
                if id_ not in results and len(results) < limit:
                    patient = next((p for p in all_patients if p.id == id_), None)
                    if patient:
                        results[patient.id] = (patient, score, 'phonetic')

        # Sort by score and return
        sorted_results = sorted(results.values(), key=lambda x: -x[1])
        return sorted_results[:limit]

    def _search_uhid(self, query: str):
        """Search by UHID."""
        # Try exact match first
        results = self.db.search_patients_basic(query)
        return [p for p in results if p.uhid and query.upper() in p.uhid.upper()]


# Convenience function for quick phonetic code generation
def get_phonetic_code(name: str) -> str:
    """Get phonetic code for a name."""
    return IndianPhoneticSearch().get_phonetic_code(name)


# Test cases
if __name__ == "__main__":
    phonetic = IndianPhoneticSearch()

    test_names = [
        ("Ram", "Raam"),
        ("Ram", "Rama"),
        ("Shailesh", "Shylesh"),
        ("Shailesh", "Shailash"),
        ("Pradeep", "Pradip"),
        ("Vijay", "Wijay"),
        ("Bharat", "Barat"),
        ("Gaurav", "Gorav"),
        ("Suresh", "Sooresh"),
        ("Dhiraj", "Diraj"),
    ]

    print("Phonetic Code Tests:")
    print("=" * 60)
    for name1, name2 in test_names:
        code1 = phonetic.get_phonetic_code(name1)
        code2 = phonetic.get_phonetic_code(name2)
        score = phonetic.match_score(name1, name2)
        match = "✓" if code1 == code2 else "≈" if score > 0.7 else "✗"
        print(f"{name1:15} → {code1:10} | {name2:15} → {code2:10} | {match} ({score:.2f})")
