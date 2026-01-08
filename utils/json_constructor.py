# import re
# import json

# # def md_to_flat_json(text, title, phase):
# #     # 1. Define Regex to capture: Level (#), Number (1.1.), and Title
# #     # Pattern explanation: Start of line, hashtags, space, numbers/dots, space, title
# #     heading_pattern = re.compile(r'^(#+)\s+([\d\.]+)\s+(.*)$')
    
# #     lines = text.split('\n')
    
# #     # Flat list to hold parsed sections temporarily
# #     flat_sections = []
    
# #     current_section = None
    
# #     for line in lines:
# #         line = line.strip()
# #         if not line:
# #             continue # Skip empty lines
            
# #         match = heading_pattern.match(line)
        
# #         if match:
# #             # We found a new heading
# #             # Save the previous section if it exists
# #             if current_section:
# #                 flat_sections.append(current_section)
            
# #             # Create new section object
# #             current_section = {
# #                 "number": match.group(2).strip(),
# #                 "title": match.group(3).strip(),
# #                 "level": len(match.group(1)), # Count of #
# #                 "own_content": [], # Text that belongs strictly to this header
# #                 "children": []
# #             }
# #         else:
# #             # This is body text
# #             if current_section:
# #                 current_section['own_content'].append(line)
    
# #     # Append the last section
# #     if current_section:
# #         flat_sections.append(current_section)

# #     # 2. Build the Tree Structure (Nesting)
# #     # We use a dictionary map for easy lookup by section number
# #     section_map = {}
# #     root_nodes = []

# #     # Initialize map and clean up numbers (ensure trailing dots for consistency if needed)
# #     for sec in flat_sections:
# #         # Normalize number: "1" -> "1.", "1.1" -> "1.1." to allow prefix matching
# #         norm_num = sec['number']
# #         if not norm_num.endswith('.'):
# #             norm_num += '.'
        
# #         # Store in map
# #         section_map[norm_num] = sec
        
# #         # Logic to find parent
# #         # If number is "5.2.1.", parent is "5.2."
# #         parts = norm_num.strip('.').split('.')
        
# #         # if len(parts) == 1:
# #         #     # It's a top level node (e.g., 1., 2., 5.)
# #         #     root_nodes.append(sec)
# #         # else:
# #         #     # It is a child. Construct parent key.
# #         #     # Pop the last part to get parent. 
# #         #     parent_key = ".".join(parts[:-1]) + "."
            
# #         #     if parent_key in section_map:
# #         #         section_map[parent_key]['children'].append(sec)
# #         #     else:
# #         #         # Fallback: if parent not found (malformed doc), treat as root
# #         #         root_nodes.append(sec)

# #         for sec in flat_sections:
# #                 norm_num = sec['key']
# #                 parts = norm_num.strip('.').split('.') # e.g. "9.1.2." -> ['9', '1', '2']
                
# #                 parent_found = False
                
# #                 # Logic: If we are '9.1.2', we try to find '9.1.' first. 
# #                 # If '9.1.' doesn't exist, we try '9.'.
# #                 # We loop backwards from the immediate parent up to the top level.
# #                 if len(parts) > 1:
# #                     for i in range(len(parts) - 1, 0, -1):
# #                         # Construct potential parent key
# #                         # i=2 -> parts[:2] -> 9.1
# #                         # i=1 -> parts[:1] -> 9
# #                         potential_parent_key = ".".join(parts[:i]) + "."
                        
# #                         if potential_parent_key in section_map:
# #                             section_map[potential_parent_key]['children'].append(sec)
# #                             parent_found = True
# #                             break # Stop once we attach to the nearest existing ancestor
                
# #                 # If no parent was found in the chain (or it's a top level node like "9.")
# #                 if not parent_found:
# #                     root_nodes.append(sec)

# import re
# import json

# def md_to_flat_json(text, title, phase):
#     # 1. Define Regex
#     heading_pattern = re.compile(r'^(#+)\s+([\d\.]+)\s+(.*)$')
    
#     lines = text.split('\n')
#     flat_sections = []
#     current_section = None
    
#     # --- PARSING FLAT LIST (Same as before) ---
#     for line in lines:
#         line = line.strip()
#         if not line:
#             continue 
            
#         match = heading_pattern.match(line)
        
#         if match:
#             if current_section:
#                 flat_sections.append(current_section)
            
#             current_section = {
#                 "number": match.group(2).strip(),
#                 "title": match.group(3).strip(),
#                 "level": len(match.group(1)),
#                 "own_content": [],
#                 "children": []
#             }
#         else:
#             if current_section:
#                 current_section['own_content'].append(line)
    
#     if current_section:
#         flat_sections.append(current_section)

#     # --- 2. BUILD TREE STRUCTURE (UPDATED LOGIC) ---
#     section_map = {}
#     root_nodes = []

#     # First pass: Populate the map
#     for sec in flat_sections:
#         # Normalize number to ensure it ends with '.' for consistent key lookup
#         norm_num = sec['number']
#         if not norm_num.endswith('.'):
#             norm_num += '.'
        
#         sec['key'] = norm_num # Store the normalized key for reference
#         section_map[norm_num] = sec

#     # Second pass: Link children to the NEAREST ancestor
#     for sec in flat_sections:
#         norm_num = sec['key']
#         parts = norm_num.strip('.').split('.') # e.g. "9.1.2." -> ['9', '1', '2']
        
#         parent_found = False
        
#         # Logic: If we are '9.1.2', we try to find '9.1.' first. 
#         # If '9.1.' doesn't exist, we try '9.'.
#         # We loop backwards from the immediate parent up to the top level.
#         if len(parts) > 1:
#             for i in range(len(parts) - 1, 0, -1):
#                 # Construct potential parent key
#                 # i=2 -> parts[:2] -> 9.1
#                 # i=1 -> parts[:1] -> 9
#                 potential_parent_key = ".".join(parts[:i]) + "."
                
#                 if potential_parent_key in section_map:
#                     section_map[potential_parent_key]['children'].append(sec)
#                     parent_found = True
#                     break # Stop once we attach to the nearest existing ancestor
        
#         # If no parent was found in the chain (or it's a top level node like "9.")
#         if not parent_found:
#             root_nodes.append(sec)

#     # --- RECURSIVE BUILD (Same as before) ---
#     def build_nested_structure(node):
#         local_text = "\n".join(node['own_content'])
        
#         children_text = ""
#         processed_children = []
        
#         for child in node['children']:
#             child_data = build_nested_structure(child)
            
#             # Combine Number and Title for the header inside the body
#             child_header = f"{child_data['section_number']} {child_data['title']}"
            
#             children_text += f"\n\n{child_header}\n{child_data['body']}"
            
#             processed_children.append(child_data)
        
#         full_body = (local_text + children_text).strip()
        
#         return {
#             "section_number": node['number'],
#             "title": node['title'],
#             "body": full_body,
#             "subsections": processed_children
#         }

#     nested_data = [build_nested_structure(root) for root in root_nodes]
    
#     # --- 3. FLATTEN FOR OUTPUT (Same as before) ---
#     final_flat_list = []

#     def flatten_recursive(nodes):
#         for node in nodes:
#             if phase:
#                 formatted_title = f"Generate section {node['section_number']} {node['title']} of a {phase} clinical protocol: {title}"
#             else:
#                 formatted_title = f"Generate section {node['section_number']} {node['title']} of a clinical protocol: {title}"
            
#             final_flat_list.append({
#                 "instruction": formatted_title,
#                 "input": "",
#                 "output": node['body']
#             })
            
#             if node.get('subsections'):
#                 flatten_recursive(node['subsections'])

#     flatten_recursive(nested_data)
    
#     return final_flat_list



#     # Recursive function to aggregate text
#     def build_nested_structure(node):
#         # 1. Get the text strictly belonging to this node
#         local_text = "\n".join(node['own_content'])
        
#         children_text = ""
#         processed_children = []
        
#         for child in node['children']:
#             child_data = build_nested_structure(child)
            
#             child_header = f"{child_data['section_number']} {child_data['title']}"
            
#             # Append: Newlines + Header + Newline + Body
#             children_text += f"\n\n{child_header}\n{child_data['body']}"
            
#             processed_children.append(child_data)
        
#         # Combine local text with the formatted children text
#         full_body = (local_text + children_text).strip()
        
#         return {
#             "section_number": node['number'],
#             "title": node['title'],
#             "body": full_body,
#             "subsections": processed_children
#         }

#     nested_data = [build_nested_structure(root) for root in root_nodes]
    
#     # ==========================================
#     # STEP 3: FLATTEN (Convert Tree to Single Level List)
#     # ==========================================
#     final_flat_list = []

#     def flatten_recursive(nodes):
#         for node in nodes:
#             # Create the formatted title: "Number Title"
#             if phase:
#                 formatted_title = f"Generate section {node['section_number']} {node['title']} of a {phase} clinical protocol: {title}"
#             else:
#                 formatted_title = f"Generate section {node['section_number']} {node['title']} of a clinical protocol: {title}"
            
#             # Append to master list
#             final_flat_list.append({
#                 "instruction": formatted_title,
#                 "input": "",
#                 "output": node['body']
#             })
            
#             # If there are subsections, recurse into them so they get added to the list too
#             if node.get('subsections'):
#                 flatten_recursive(node['subsections'])

#     flatten_recursive(nested_data)
    
#     return final_flat_list

import re
import json

def md_to_flat_json(text, title, phase):
    # 1. Define Regex
    # Pattern explanation:
    # ^\s*      -> Allow for indentation
    # (#+)      -> Capture the Markdown level (e.g., ##)
    # \s+       -> Required space
    # ([\d\.]+) -> Capture the number (e.g., 9., 9.1.2)
    # \s*       -> Optional space
    # (.*)$     -> Capture the Title
    heading_pattern = re.compile(r'^\s*(#+)\s+([\d\.]+)\s*(.*)$')
    
    lines = text.split('\n')
    flat_sections = []
    current_section = None
    
    # ==========================================
    # PHASE 1: LINEAR PARSING
    # Extract headers and body content into a flat list
    # ==========================================
    for line in lines:
        line = line.strip()
        # Regex match
        match = heading_pattern.match(line)
        
        if match:
            # New Heading Found -> Save previous section
            if current_section:
                flat_sections.append(current_section)
            
            # Normalize the number: "9" -> "9.", "9.1" -> "9.1."
            # This ensures consistent prefix matching later.
            raw_num = match.group(2).strip()
            norm_num = raw_num if raw_num.endswith('.') else raw_num + '.'
            
            current_section = {
                "number": raw_num,       # For display
                "norm_number": norm_num, # For logic (e.g., "9.1.2.")
                "title": match.group(3).strip(),
                "level": len(match.group(1)),
                "own_content": [],
                "children": []
            }
        else:
            # Body text -> append to current section
            if current_section:
                if line: # Only append non-empty lines to keep clean
                    current_section['own_content'].append(line)
    
    # Append the final section found
    if current_section:
        flat_sections.append(current_section)

    # ==========================================
    # PHASE 2: TREE BUILDING (LINEAR LOOK-BACK)
    # Handles Skip Sections & Duplicate Section Numbers
    # ==========================================
    root_nodes = []

    # Iterate through every section found
    for i, section in enumerate(flat_sections):
        parent_found = False
        child_num = section['norm_number'] # e.g., "9.1.2."
        
        # Look BACKWARDS from the current position (i-1) down to 0
        for j in range(i - 1, -1, -1):
            potential_parent = flat_sections[j]
            parent_num = potential_parent['norm_number'] # e.g., "9."
            
            # LOGIC:
            # 1. The child number must start with the parent number (Prefix Check).
            #    e.g. "9.1.2." starts with "9." -> True
            # 2. They must not be the exact same number (prevents attaching duplicate sibling to sibling).
            #    e.g. "1." starts with "1." -> True, but we ignore it.
            if child_num.startswith(parent_num) and child_num != parent_num:
                # We found the nearest ancestor!
                # Attach this section to that parent
                potential_parent['children'].append(section)
                parent_found = True
                
                # BREAK: Important! We found the immediate relevant parent.
                # Stop searching so we don't attach to a "Grandparent" or a duplicate 
                # section from the start of the file.
                break 
        
        # If no parent was found in the previous lines, this is a Root Node (Top Level)
        if not parent_found:
            root_nodes.append(section)

    # ==========================================
    # PHASE 3: RECURSIVE CONTENT GENERATION
    # Combine Parent Content + Formatted Child Content
    # ==========================================
    def build_nested_structure(node):
        # 1. Get the text strictly belonging to this node
        local_text = "\n".join(node['own_content'])
        
        children_text = ""
        processed_children = []
        
        for child in node['children']:
            child_data = build_nested_structure(child)
            
            # Format: "9.1.2. Secondary Efficacy Assessments"
            child_header = f"{child_data['section_number']} {child_data['title']}"
            
            # Format Body: Header + Content
            children_text += f"\n\n{child_header}\n{child_data['body']}"
            
            processed_children.append(child_data)
        
        # Combine: Local Text + All Children Text
        full_body = (local_text + children_text).strip()
        
        return {
            "section_number": node['number'],
            "title": node['title'],
            "body": full_body,
            "subsections": processed_children
        }

    # Process all root nodes
    nested_data = [build_nested_structure(root) for root in root_nodes]
    
    # ==========================================
    # PHASE 4: FLATTEN FOR OUTPUT
    # ==========================================
    final_flat_list = []

    def flatten_recursive(nodes):
        for node in nodes:
            # Format instruction
            if phase:
                formatted_instruction = f"Generate section {node['section_number']} {node['title']} of a {phase} clinical protocol: {title}"
            else:
                formatted_instruction = f"Generate section {node['section_number']} {node['title']} of a clinical protocol: {title}"
            
            final_flat_list.append({
                "instruction": formatted_instruction,
                "input": "",
                "output": node['body']
            })
            
            # Recurse to add children as their own entries in the dataset
            if node.get('subsections'):
                flatten_recursive(node['subsections'])

    flatten_recursive(nested_data)
    
    return final_flat_list