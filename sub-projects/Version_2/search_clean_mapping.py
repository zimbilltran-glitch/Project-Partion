import os

def search_text_mapping():
    path = r'd:\Project_partial\Finsang\sub-projects\Version_2\field_mapping_clean.txt'
    output_path = r'd:\Project_partial\Finsang\sub-projects\Version_2\search_results_mapping.txt'
    terms = ["vốn chủ sở hữu", "thu nhập hoạt động", "chi phí quản lý", "cho vay khách hàng", "tiền gửi của khách hàng", "cho vay ký quỹ", "môi giới"]
    
    results = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line_lower = line.lower()
            for term in terms:
                if term in line_lower:
                    results.append(line.strip())
                    break
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for res in results:
            f.write(res + "\n")

if __name__ == "__main__":
    search_text_mapping()
