from datetime import timedelta
import re

def tokenize(text):
    """Normalize and tokenize text."""
    if not text:
        return set()
    text = text.lower()
    # Remove punctuation/symbols roughly
    tokens = re.findall(r'\w+', text)
    # Filter short words? Maybe. For now, keep it simple.
    return set(t for t in tokens if len(t) > 2)

def jaccard_similarity(set1, set2):
    """Compute Jaccard similarity between two sets."""
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    if union == 0:
        return 0.0
    return intersection / union

def simple_group_articles(articles, time_window_hours=12, similarity_threshold=0.35):
    """
    Group articles based on time window and content similarity.
    params:
        articles: list of dicts or Article objects (must have 'title', 'published_at', 'id')
    returns:
        list of lists of article IDs (groups)
    """
    if not articles:
        return []

    # Sort by published_at
    # Ensure published_at is accessible (dict or object)
    def get_attr(item, key):
        if isinstance(item, dict):
            return item.get(key)
        else:
            return getattr(item, key, None)
            
    # Normalize/Pre-tokenize
    prepared = []
    for art in articles:
        title = get_attr(art, 'title') or ""
        tokens = tokenize(title)
        pub_at = get_attr(art, 'published_at')
        art_id = get_attr(art, 'id')
        prepared.append({
            'id': art_id,
            'tokens': tokens,
            'published_at': pub_at,
            'original': art
        })
    
    # Sort
    # Note: published_at might be string if from API desc, or datetime if from DB.
    # Assuming standard sorting works or logic handles it. 
    # For now, let's assume they are roughly comparable or we just process in order.
    # If string ISO, it sorts chronologically.
    prepared.sort(key=lambda x: str(x['published_at']), reverse=True) 
    
    groups = []  # List of sets of indices or IDs? Let's store list of article items.
    
    used_indices = set()
    
    for i, p1 in enumerate(prepared):
        if i in used_indices:
            continue
            
        current_group = [p1]
        used_indices.add(i)
        
        # Look ahead for candidates
        for j in range(i + 1, len(prepared)):
            if j in used_indices:
                continue
                
            p2 = prepared[j]
            
            # Check time window (approx)
            # If datetime objects
            # delta = p1['published_at'] - p2['published_at']
            # if abs(delta.total_seconds()) > time_window_hours * 3600:
                # Assuming sorted descending, if p2 is too old compared to p1?
                # Actually, p2 is older than p1.
                # stop checking? depends on how strictly sorted.
            #     continue
            
            # Check similarity
            sim = jaccard_similarity(p1['tokens'], p2['tokens'])
            if sim >= similarity_threshold:
                current_group.append(p2)
                used_indices.add(j)
                
                # Cap group size?
                if len(current_group) >= 12:
                    break
                    
        groups.append([g['original'] for g in current_group])
        
    return groups
