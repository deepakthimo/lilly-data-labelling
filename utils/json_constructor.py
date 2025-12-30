import re
import json

def md_to_flat_json(text, title, phase):
    # 1. Define Regex to capture: Level (#), Number (1.1.), and Title
    # Pattern explanation: Start of line, hashtags, space, numbers/dots, space, title
    heading_pattern = re.compile(r'^(#+)\s+([\d\.]+)\s+(.*)$')
    
    lines = text.split('\n')
    
    # Flat list to hold parsed sections temporarily
    flat_sections = []
    
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue # Skip empty lines
            
        match = heading_pattern.match(line)
        
        if match:
            # We found a new heading
            # Save the previous section if it exists
            if current_section:
                flat_sections.append(current_section)
            
            # Create new section object
            current_section = {
                "number": match.group(2).strip(),
                "title": match.group(3).strip(),
                "level": len(match.group(1)), # Count of #
                "own_content": [], # Text that belongs strictly to this header
                "children": []
            }
        else:
            # This is body text
            if current_section:
                current_section['own_content'].append(line)
    
    # Append the last section
    if current_section:
        flat_sections.append(current_section)

    # 2. Build the Tree Structure (Nesting)
    # We use a dictionary map for easy lookup by section number
    section_map = {}
    root_nodes = []

    # Initialize map and clean up numbers (ensure trailing dots for consistency if needed)
    for sec in flat_sections:
        # Normalize number: "1" -> "1.", "1.1" -> "1.1." to allow prefix matching
        norm_num = sec['number']
        if not norm_num.endswith('.'):
            norm_num += '.'
        
        # Store in map
        section_map[norm_num] = sec
        
        # Logic to find parent
        # If number is "5.2.1.", parent is "5.2."
        parts = norm_num.strip('.').split('.')
        
        if len(parts) == 1:
            # It's a top level node (e.g., 1., 2., 5.)
            root_nodes.append(sec)
        else:
            # It is a child. Construct parent key.
            # Pop the last part to get parent. 
            parent_key = ".".join(parts[:-1]) + "."
            
            if parent_key in section_map:
                section_map[parent_key]['children'].append(sec)
            else:
                # Fallback: if parent not found (malformed doc), treat as root
                root_nodes.append(sec)


    # Recursive function to aggregate text
    def build_nested_structure(node):
        # 1. Get the text strictly belonging to this node
        local_text = "\n".join(node['own_content'])
        
        children_text = ""
        processed_children = []
        
        for child in node['children']:
            child_data = build_nested_structure(child)
            
            child_header = f"{child_data['section_number']} {child_data['title']}"
            
            # Append: Newlines + Header + Newline + Body
            children_text += f"\n\n{child_header}\n{child_data['body']}"
            
            processed_children.append(child_data)
        
        # Combine local text with the formatted children text
        full_body = (local_text + children_text).strip()
        
        return {
            "section_number": node['number'],
            "title": node['title'],
            "body": full_body,
            "subsections": processed_children
        }

    nested_data = [build_nested_structure(root) for root in root_nodes]
    
    # ==========================================
    # STEP 3: FLATTEN (Convert Tree to Single Level List)
    # ==========================================
    final_flat_list = []

    def flatten_recursive(nodes):
        for node in nodes:
            # Create the formatted title: "Number Title"
            if phase:
                formatted_title = f"Generate section {node['section_number']} {node['title']} of a {phase} clinical protocol: {title}"
            else:
                formatted_title = f"Generate section {node['section_number']} {node['title']} of a clinical protocol: {title}"
            
            # Append to master list
            final_flat_list.append({
                "instruction": formatted_title,
                "input": "",
                "output": node['body']
            })
            
            # If there are subsections, recurse into them so they get added to the list too
            if node.get('subsections'):
                flatten_recursive(node['subsections'])

    flatten_recursive(nested_data)
    
    return final_flat_list