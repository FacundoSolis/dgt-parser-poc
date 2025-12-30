"""
Streamlit Web App for DGT Parser POC
"""

import streamlit as st
import tempfile
import os
import pandas as pd
from pathlib import Path
import sys

# Add src to path
sys.path.append('src')

from pdf_parser import DGTParser
from business_logic import BusinessLogic

# Page config
st.set_page_config(
    page_title="DGT Parser POC",
    page_icon="🚛",
    layout="wide"
)

# Title
st.title("🚛 DGT Vehicle Report Processor")
st.markdown("**POC** - Proof of Concept for Travis Dayton")

st.markdown("---")

# Sidebar - Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    cliente_nif = st.text_input(
        "Client NIF/CIF (Optional)",
        placeholder="EMPRESA SL",
        help="Leave empty to process all vehicles"
    )
    
    st.markdown("---")
    st.info("📋 **Instructions:**\n\n1. Upload DGT PDF reports\n2. Click 'Process PDFs'\n3. View results table\n4. Download CSV")

# File uploader
st.header("📄 Upload DGT Reports")
uploaded_files = st.file_uploader(
    "Drop PDF files here or click to browse",
    type=['pdf'],
    accept_multiple_files=True,
    help="Upload one or more DGT 'Informe del Vehículo' PDFs"
)

if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} PDF(s) uploaded")
    
    # Show uploaded files
    with st.expander("📋 Uploaded Files"):
        for file in uploaded_files:
            st.text(f"• {file.name} ({file.size / 1024:.1f} KB)")

# Process button
if st.button("🚀 Process PDFs", type="primary", disabled=not uploaded_files):
    
    # Create temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Save uploaded files
        pdf_paths = []
        for i, uploaded_file in enumerate(uploaded_files):
            file_path = os.path.join(tmpdir, uploaded_file.name)
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getvalue())
            pdf_paths.append(file_path)
        
        # Initialize business logic
        logic = BusinessLogic(cliente_nif=cliente_nif if cliente_nif else None)
        
        # Process PDFs
        results = []
        for i, pdf_path in enumerate(pdf_paths):
            
            # Update progress
            progress = (i + 1) / len(pdf_paths)
            progress_bar.progress(progress)
            status_text.text(f"Processing {Path(pdf_path).name}... ({i+1}/{len(pdf_paths)})")
            
            try:
                # Parse PDF
                parser = DGTParser(pdf_path)
                data = parser.parse()
                
                # Apply business logic
                result = logic.process_vehicle(data)
                
                # Format for display
                row = {
                    'Matrícula': result['matricula'],
                    'Fecha penúlti': result['fecha_penulti'].strftime('%d/%m/%Y') if result['fecha_penulti'] else '-',
                    'Lectura k (penúlti)': result['lectura_k_penulti'],
                    'Fecha últ': result['fecha_ult'].strftime('%d/%m/%Y') if result['fecha_ult'] else '-',
                    'Lectura k (últ)': result['lectura_k_ult'],
                    'Días entre': result['dias_entre'],
                    'km ITVs': result['km_itvs'],
                    'km 1 año': result['km_1_ano'],
                    'km int': result['km_int'],
                    'km nac': result['km_nac'],
                    'Comentarios': '; '.join(result['comentarios']) if result['comentarios'] else ''
                }
                
                results.append(row)
                
            except Exception as e:
                st.error(f"❌ Error processing {Path(pdf_path).name}: {str(e)}")
        
        # Clear progress
        progress_bar.empty()
        status_text.empty()
        
        # Display results
        if results:
            st.markdown("---")
            st.header("📊 Results")
            
            # Convert to DataFrame
            df = pd.DataFrame(results)
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Vehicles", len(df))
            with col2:
                has_calculations = df['km 1 año'] > 0
                st.metric("With Calculations", has_calculations.sum())
            with col3:
                no_comments = df['Comentarios'] == ''
                st.metric("Ready to Process", no_comments.sum())
            
            st.markdown("---")
            
            # Results table
            st.dataframe(
                df,
                use_container_width=True,
                height=400
            )
            
            # Download button
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name="dgt_results.csv",
                mime="text/csv"
            )
            
            # Show details in expanders
            st.markdown("---")
            st.subheader("🔍 Vehicle Details")
            
            for idx, row in df.iterrows():
                with st.expander(f"🚗 {row['Matrícula']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Última ITV:**")
                        st.text(f"Fecha: {row['Fecha últ']}")
                        st.text(f"Kilómetros: {row['Lectura k (últ)']:,}" if row['Lectura k (últ)'] > 0 else "N/A")
                    
                    with col2:
                        st.markdown("**Penúltima ITV:**")
                        st.text(f"Fecha: {row['Fecha penúlti']}")
                        st.text(f"Kilómetros: {row['Lectura k (penúlti)']:,}" if row['Lectura k (penúlti)'] > 0 else "N/A")
                    
                    if row['km 1 año'] > 0:
                        st.markdown(f"**Proyección anual:** {row['km 1 año']:,} km/año")
                    
                    if row['Comentarios']:
                        st.warning(f"⚠️ {row['Comentarios']}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; padding: 20px;'>
    <p><strong>DGT Parser POC</strong> - Developed by Facundo Solis for Travis Dayton</p>
    <p>Technology: Python + pdfplumber + pandas</p>
</div>
""", unsafe_allow_html=True)