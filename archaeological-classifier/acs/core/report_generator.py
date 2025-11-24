"""
PDF Report Generation Module
=============================

Generates comprehensive PDF reports for archaeological artifact analysis.
"""

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from datetime import datetime
import os
import tempfile
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Optional
import json

# Import mesh renderer for real 3D renders
from acs.core.mesh_renderer import render_artifact_image, get_mesh_renderer


class ReportGenerator:
    """
    Generate PDF reports for artifact analysis and comparisons.
    """

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Create custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))

        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#4a5568'),
            spaceAfter=20,
            spaceBefore=15
        ))

        # Section heading
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=10,
            spaceBefore=15,
            borderPadding=5
        ))

        # Info text
        self.styles.add(ParagraphStyle(
            name='InfoText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#718096'),
            alignment=TA_CENTER
        ))

    def _create_header_footer(self, canvas_obj, doc):
        """Add header and footer to each page."""
        canvas_obj.saveState()

        # Header
        canvas_obj.setFont('Helvetica-Bold', 10)
        canvas_obj.setFillColor(colors.HexColor('#667eea'))
        canvas_obj.drawString(inch, A4[1] - 0.5*inch,
                             "Archaeological Classifier System")

        # Footer
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(colors.grey)
        canvas_obj.drawString(inch, 0.5*inch,
                             f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        canvas_obj.drawRightString(A4[0] - inch, 0.5*inch,
                                   f"Page {doc.page}")

        canvas_obj.restoreState()

    def generate_comparison_report(self, artifact1, artifact2, mesh1, mesh2,
                                   features1, features2, style1=None, style2=None):
        """
        Generate a comprehensive comparison report for two artifacts.

        Args:
            artifact1: ID of first artifact
            artifact2: ID of second artifact
            mesh1: Trimesh object of first artifact
            mesh2: Trimesh object of second artifact
            features1: Feature dict of first artifact
            features2: Feature dict of second artifact
            style1: Optional stylistic features of first artifact
            style2: Optional stylistic features of second artifact

        Returns:
            Path to generated PDF file
        """
        # Create temporary file for PDF
        temp_dir = tempfile.gettempdir()
        pdf_filename = f"comparison_report_{artifact1}_{artifact2}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(temp_dir, pdf_filename)

        # Create PDF document
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch
        )

        # Container for PDF elements
        story = []

        # Title
        title = Paragraph(
            f"Artifact Comparison Report",
            self.styles['CustomTitle']
        )
        story.append(title)

        # Report info
        report_info = Paragraph(
            f"Comparing: <b>{artifact1}</b> vs <b>{artifact2}</b><br/>"
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            self.styles['InfoText']
        )
        story.append(report_info)
        story.append(Spacer(1, 0.5*inch))

        # Executive Summary
        story.append(Paragraph("Executive Summary", self.styles['SectionHeading']))

        similarity_score = self._calculate_similarity(features1, features2)
        summary_text = f"""
        This report presents a comprehensive comparison between artifacts
        <b>{artifact1}</b> and <b>{artifact2}</b>.
        The overall similarity score is <b>{similarity_score:.1%}</b>.
        """
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 0.3*inch))

        # Feature Comparison Table
        story.append(Paragraph("Morphometric Features", self.styles['SectionHeading']))
        feature_table = self._create_feature_comparison_table(features1, features2)
        story.append(feature_table)
        story.append(Spacer(1, 0.3*inch))

        # Geometric Properties
        story.append(Paragraph("Geometric Properties", self.styles['SectionHeading']))
        geom_table = self._create_geometry_table(mesh1, mesh2, artifact1, artifact2)
        story.append(geom_table)
        story.append(Spacer(1, 0.3*inch))

        # Stylistic Analysis (if available)
        if style1 and style2:
            story.append(Paragraph("Stylistic Analysis", self.styles['SectionHeading']))
            style_table = self._create_stylistic_comparison_table(style1, style2)
            story.append(style_table)
            story.append(Spacer(1, 0.2*inch))

            style_summary = self._create_stylistic_summary(style1, style2)
            story.append(Paragraph(style_summary, self.styles['Normal']))
            story.append(Spacer(1, 0.3*inch))

        # Technical Drawings Section
        story.append(PageBreak())
        story.append(Paragraph("Disegni Tecnici Archeologici", self.styles['SectionHeading']))
        story.append(Paragraph(
            "Documentazione grafica professionale secondo convenzioni archeologiche standard "
            "per asce dell'Età del Bronzo.",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 0.2*inch))

        # Generate technical drawings for both artifacts
        # IMPORTANT: Use multiprocessing worker to avoid macOS matplotlib threading issues
        try:
            from acs.core.drawing_worker import generate_drawing_safe
            import io

            # Artifact 1 drawings
            story.append(Paragraph(f"Artifact {artifact1}", self.styles['SubHeading']))
            img1_data = generate_drawing_safe(mesh1, artifact1, features1, 'complete_sheet', timeout=90)
            img1_path = self._save_temp_image(img1_data)
            if img1_path:
                story.append(Image(img1_path, width=7*inch, height=9*inch))
                story.append(Spacer(1, 0.2*inch))

            story.append(PageBreak())

            # Artifact 2 drawings
            story.append(Paragraph(f"Artifact {artifact2}", self.styles['SubHeading']))
            img2_data = generate_drawing_safe(mesh2, artifact2, features2, 'complete_sheet', timeout=90)
            img2_path = self._save_temp_image(img2_data)
            if img2_path:
                story.append(Image(img2_path, width=7*inch, height=9*inch))
                story.append(Spacer(1, 0.2*inch))

        except Exception as e:
            import traceback
            print(f"Warning: Technical drawings generation failed: {str(e)}")
            print(traceback.format_exc())
            story.append(Paragraph(
                f"<i>Nota: Impossibile generare disegni tecnici ({str(e)})</i>",
                self.styles['Normal']
            ))

        # Statistical Analysis
        story.append(Paragraph("Statistical Analysis", self.styles['SectionHeading']))
        stats_chart_path = self._create_statistics_chart(features1, features2, artifact1, artifact2)
        if stats_chart_path:
            story.append(Image(stats_chart_path, width=5*inch, height=3*inch))
            story.append(Spacer(1, 0.3*inch))

        # Similarity Analysis
        story.append(PageBreak())
        story.append(Paragraph("Detailed Similarity Analysis", self.styles['SectionHeading']))

        similarity_details = self._analyze_similarity_details(features1, features2)
        for detail in similarity_details:
            story.append(Paragraph(detail, self.styles['Normal']))
            story.append(Spacer(1, 0.1*inch))

        # Recommendations
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("Interpretation & Recommendations", self.styles['SectionHeading']))

        recommendations = self._generate_recommendations(similarity_score, features1, features2)
        for rec in recommendations:
            story.append(Paragraph(f"• {rec}", self.styles['Normal']))
            story.append(Spacer(1, 0.1*inch))

        # Technical Details
        story.append(PageBreak())
        story.append(Paragraph("Technical Details", self.styles['SectionHeading']))

        tech_details = f"""
        <b>Analysis Method:</b> Morphometric feature comparison<br/>
        <b>Feature Set:</b> Volume, Surface Area, Length, Width, Height, Compactness<br/>
        <b>Similarity Metric:</b> Normalized feature distance<br/>
        <b>Mesh Processing:</b> Trimesh library v3.x<br/>
        """
        story.append(Paragraph(tech_details, self.styles['Normal']))

        # Build PDF
        doc.build(story, onFirstPage=self._create_header_footer,
                 onLaterPages=self._create_header_footer)

        # Clean up temporary chart files
        if stats_chart_path and os.path.exists(stats_chart_path):
            try:
                os.remove(stats_chart_path)
            except:
                pass

        return pdf_path

    def _save_temp_image(self, image_bytes: bytes) -> str:
        """
        Save image bytes to temporary file for PDF inclusion.

        Args:
            image_bytes: Image data as bytes

        Returns:
            Path to temporary image file
        """
        import io
        temp_dir = tempfile.gettempdir()
        temp_filename = f"technical_drawing_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
        temp_path = os.path.join(temp_dir, temp_filename)

        with open(temp_path, 'wb') as f:
            f.write(image_bytes)

        return temp_path

    def _calculate_similarity(self, features1, features2):
        """Calculate overall similarity score."""
        feature_keys = ['volume', 'surface_area', 'length', 'width', 'height', 'compactness']

        similarities = []
        for key in feature_keys:
            if key in features1 and key in features2:
                val1 = features1[key]
                val2 = features2[key]
                if max(val1, val2) > 0:
                    similarity = 1 - abs(val1 - val2) / max(val1, val2)
                    similarities.append(similarity)

        return np.mean(similarities) if similarities else 0.0

    def _create_feature_comparison_table(self, features1, features2):
        """Create a table comparing morphometric features."""
        feature_keys = [
            ('volume', 'Volume', 'mm³'),
            ('surface_area', 'Surface Area', 'mm²'),
            ('length', 'Length', 'mm'),
            ('width', 'Width', 'mm'),
            ('height', 'Height', 'mm'),
            ('compactness', 'Compactness', ''),
        ]

        data = [['Feature', 'Artifact 1', 'Artifact 2', 'Difference (%)']]

        for key, label, unit in feature_keys:
            if key in features1 and key in features2:
                val1 = features1[key]
                val2 = features2[key]
                diff_pct = abs(val1 - val2) / max(val1, val2) * 100 if max(val1, val2) > 0 else 0

                unit_str = f" {unit}" if unit else ""
                data.append([
                    label,
                    f"{val1:.2f}{unit_str}",
                    f"{val2:.2f}{unit_str}",
                    f"{diff_pct:.1f}%"
                ])

        table = Table(data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
        ]))

        return table

    def _create_geometry_table(self, mesh1, mesh2, artifact1, artifact2):
        """Create table with geometric mesh properties."""
        data = [
            ['Property', artifact1, artifact2],
            ['Vertices', f"{len(mesh1.vertices):,}", f"{len(mesh2.vertices):,}"],
            ['Faces', f"{len(mesh1.faces):,}", f"{len(mesh2.faces):,}"],
            ['Is Watertight', 'Yes' if mesh1.is_watertight else 'No',
             'Yes' if mesh2.is_watertight else 'No'],
        ]

        table = Table(data, colWidths=[2*inch, 2*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#764ba2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
        ]))

        return table

    def _create_statistics_chart(self, features1, features2, artifact1, artifact2):
        """Create a bar chart comparing features."""
        try:
            feature_keys = ['volume', 'surface_area', 'length', 'width', 'height']
            label_map = {
                'volume': 'Volume',
                'surface_area': 'Surface\nArea',
                'length': 'Length',
                'width': 'Width',
                'height': 'Height'
            }

            # Normalize values for comparison and build labels dynamically
            values1 = []
            values2 = []
            labels = []

            for key in feature_keys:
                if key in features1 and key in features2:
                    val1 = features1[key]
                    val2 = features2[key]
                    max_val = max(val1, val2)
                    if max_val > 0:
                        values1.append(val1 / max_val * 100)
                        values2.append(val2 / max_val * 100)
                        labels.append(label_map[key])

            if not values1:
                return None

            # Create chart
            x = np.arange(len(labels))
            width = 0.35

            fig, ax = plt.subplots(figsize=(8, 5))
            bars1 = ax.bar(x - width/2, values1, width, label=artifact1,
                          color='#667eea', alpha=0.8)
            bars2 = ax.bar(x + width/2, values2, width, label=artifact2,
                          color='#764ba2', alpha=0.8)

            ax.set_ylabel('Normalized Value (%)', fontsize=11)
            ax.set_title('Feature Comparison', fontsize=13, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(labels, fontsize=9)
            ax.legend(fontsize=10)
            ax.grid(axis='y', alpha=0.3)

            plt.tight_layout()

            # Save to temporary file
            chart_path = os.path.join(tempfile.gettempdir(),
                                     f'chart_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            plt.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close()

            return chart_path

        except Exception as e:
            import traceback
            print(f"Error creating chart: {e}")
            print(traceback.format_exc())
            return None

    def _analyze_similarity_details(self, features1, features2):
        """Generate detailed similarity analysis text."""
        details = []

        # Volume comparison
        if 'volume' in features1 and 'volume' in features2:
            v_diff = abs(features1['volume'] - features2['volume']) / max(features1['volume'], features2['volume']) * 100
            if v_diff < 5:
                details.append(f"<b>Volume:</b> Nearly identical volumes (difference: {v_diff:.1f}%), "
                             "suggesting similar overall size and material quantity.")
            elif v_diff < 15:
                details.append(f"<b>Volume:</b> Moderate volume difference ({v_diff:.1f}%), "
                             "which may indicate different casting sizes or post-casting modifications.")
            else:
                details.append(f"<b>Volume:</b> Significant volume difference ({v_diff:.1f}%), "
                             "suggesting these may represent different size classes or types.")

        # Dimensional analysis
        if all(k in features1 and k in features2 for k in ['length', 'width', 'height']):
            l_diff = abs(features1['length'] - features2['length']) / max(features1['length'], features2['length']) * 100
            w_diff = abs(features1['width'] - features2['width']) / max(features1['width'], features2['width']) * 100
            h_diff = abs(features1['height'] - features2['height']) / max(features1['height'], features2['height']) * 100

            details.append(f"<b>Dimensional Analysis:</b> Length differs by {l_diff:.1f}%, "
                         f"width by {w_diff:.1f}%, and height by {h_diff:.1f}%. "
                         f"{'Proportions are well-preserved' if max(l_diff, w_diff, h_diff) < 10 else 'Proportional differences detected'}.")

        # Compactness
        if 'compactness' in features1 and 'compactness' in features2:
            c_diff = abs(features1['compactness'] - features2['compactness'])
            details.append(f"<b>Compactness:</b> Shape compactness difference of {c_diff:.3f}. "
                         f"{'Similar shape complexity' if c_diff < 0.1 else 'Different shape profiles'}.")

        return details

    def _generate_recommendations(self, similarity_score, features1, features2):
        """Generate interpretation recommendations."""
        recs = []

        if similarity_score > 0.9:
            recs.append("<b>High Similarity (>90%):</b> These artifacts likely originate from the same "
                       "casting matrix or represent the same typological class. Consider them as variants "
                       "of the same type.")
        elif similarity_score > 0.75:
            recs.append("<b>Moderate Similarity (75-90%):</b> Artifacts show strong typological affinity. "
                       "They may come from related but distinct matrices, or represent sub-types within "
                       "the same class.")
        elif similarity_score > 0.5:
            recs.append("<b>Low Similarity (50-75%):</b> Limited morphometric correspondence. These may "
                       "represent different types or classes, though some general characteristics might "
                       "be shared.")
        else:
            recs.append("<b>Very Low Similarity (<50%):</b> Artifacts are morphometrically distinct. "
                       "They likely represent different types, functional categories, or chronological "
                       "periods.")

        recs.append("Further analysis recommended: Detailed surface inspection, metallurgical analysis, "
                   "and contextual archaeological data should complement this morphometric comparison.")

        recs.append("Consider examining wear patterns, casting flaws, and manufacturing traces for additional "
                   "insights into production techniques and use-life.")

        return recs

    def _create_stylistic_comparison_table(self, style1, style2):
        """Create a table comparing stylistic features."""
        data = [['Feature Category', 'Artifact 1', 'Artifact 2', 'Similarity']]

        # Extract key stylistic metrics
        style_metrics = [
            ('symmetry', 'overall_symmetry', 'Overall Symmetry'),
            ('proportions', 'length_width_ratio', 'Length/Width Ratio'),
            ('surface_quality', 'overall_quality', 'Surface Quality'),
            ('shape_regularity', 'radial_uniformity', 'Shape Regularity'),
            ('curvature', 'mean_curvature', 'Mean Curvature')
        ]

        for category, key, label in style_metrics:
            if category in style1 and category in style2:
                cat1 = style1[category]
                cat2 = style2[category]

                if isinstance(cat1, dict) and isinstance(cat2, dict) and key in cat1 and key in cat2:
                    val1 = cat1[key]
                    val2 = cat2[key]

                    if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                        similarity = 1 - abs(val1 - val2) / max(abs(val1), abs(val2), 1)
                        data.append([
                            label,
                            f"{val1:.3f}",
                            f"{val2:.3f}",
                            f"{similarity:.1%}"
                        ])

        table = Table(data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
        ]))

        return table

    def _create_stylistic_summary(self, style1, style2):
        """Create a textual summary of stylistic comparison."""
        summary_parts = []

        # Symmetry comparison
        if 'symmetry' in style1 and 'symmetry' in style2:
            sym1 = style1['symmetry'].get('overall_symmetry', 0)
            sym2 = style2['symmetry'].get('overall_symmetry', 0)
            if abs(sym1 - sym2) < 0.1:
                summary_parts.append("<b>Symmetry:</b> Both artifacts show similar levels of symmetry, "
                                   f"indicating comparable manufacturing precision ({sym1:.1%} vs {sym2:.1%}).")
            else:
                summary_parts.append(f"<b>Symmetry:</b> Notable difference in symmetry levels "
                                   f"({sym1:.1%} vs {sym2:.1%}), suggesting different production techniques or preservation states.")

        # Surface quality
        if 'surface_quality' in style1 and 'surface_quality' in style2:
            qual1 = style1['surface_quality'].get('overall_quality', 0)
            qual2 = style2['surface_quality'].get('overall_quality', 0)
            cat1 = style1['surface_quality'].get('quality_category', 'unknown')
            cat2 = style2['surface_quality'].get('quality_category', 'unknown')

            if cat1 == cat2:
                summary_parts.append(f"<b>Surface Quality:</b> Both artifacts exhibit {cat1.replace('_', ' ')} finish, "
                                   "suggesting similar post-casting treatment.")
            else:
                summary_parts.append(f"<b>Surface Quality:</b> Different finish levels ({cat1.replace('_', ' ')} vs {cat2.replace('_', ' ')}), "
                                   "indicating varying degrees of surface treatment or preservation.")

        # Proportions
        if 'proportions' in style1 and 'proportions' in style2:
            if 'shape_category' in style1['proportions'] and 'shape_category' in style2['proportions']:
                cat1 = style1['proportions']['shape_category']
                cat2 = style2['proportions']['shape_category']
                if cat1 == cat2:
                    summary_parts.append(f"<b>Shape Category:</b> Both artifacts classified as '{cat1}', "
                                       "indicating similar overall proportions and form.")

        return "<br/><br/>".join(summary_parts) if summary_parts else "Detailed stylistic analysis available in data tables above."

    def generate_technological_report(self,
                                      artifact_id: str,
                                      mesh,
                                      tech_features: Dict,
                                      tech_report: str,
                                      ai_interpretation: Optional[Dict] = None,
                                      morphometric_features: Optional[Dict] = None) -> str:
        """
        Generate comprehensive technological analysis report with real 3D renders.

        Args:
            artifact_id: Artifact identifier
            mesh: Trimesh object (for real 3D rendering)
            tech_features: Technological analysis features dictionary
            tech_report: Text report from technological analyzer
            ai_interpretation: Structured AI interpretation (JSON format)
            morphometric_features: Optional morphometric features

        Returns:
            Path to generated PDF file
        """
        temp_dir = tempfile.gettempdir()
        pdf_filename = f"tech_report_{artifact_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(temp_dir, pdf_filename)

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch
        )

        story = []

        # Title
        title = Paragraph(
            f"Technological Analysis Report<br/>{artifact_id}",
            self.styles['CustomTitle']
        )
        story.append(title)

        # Report metadata
        metadata = Paragraph(
            f"Archaeological Classifier System<br/>"
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
            f"Analysis Type: Bronze Age Metallurgy",
            self.styles['InfoText']
        )
        story.append(metadata)
        story.append(Spacer(1, 0.4*inch))

        # === SECTION 1: 3D RENDERS (REAL MESH VISUALIZATION) ===
        story.append(Paragraph("3D Mesh Visualization", self.styles['SectionHeading']))
        story.append(Paragraph(
            "High-quality renders generated from actual 3D mesh geometry using archaeological lighting standards.",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 0.2*inch))

        # Generate real 3D render using mesh_renderer.py
        try:
            render_path = render_artifact_image(mesh, artifact_id, output_dir=temp_dir)
            if render_path and os.path.exists(render_path):
                story.append(Image(render_path, width=6*inch, height=4.5*inch))
                story.append(Spacer(1, 0.3*inch))
            else:
                story.append(Paragraph("<i>3D render generation failed</i>", self.styles['Normal']))
        except Exception as e:
            print(f"Error generating 3D render: {e}")
            story.append(Paragraph(f"<i>3D render unavailable: {str(e)}</i>", self.styles['Normal']))

        story.append(Spacer(1, 0.2*inch))

        # === SECTION 2: AI INTERPRETATION (STRUCTURED) ===
        if ai_interpretation and isinstance(ai_interpretation, dict) and 'interpretation' in ai_interpretation:
            story.append(PageBreak())
            story.append(Paragraph("Archaeological Interpretation", self.styles['SectionHeading']))
            story.append(Paragraph(
                "Expert analysis based on technological features with temperature 0.1 for factual accuracy.",
                self.styles['Normal']
            ))
            story.append(Spacer(1, 0.2*inch))

            interp = ai_interpretation['interpretation']

            # Summary
            if 'summary' in interp:
                story.append(Paragraph("Executive Summary", self.styles['CustomSubtitle']))
                story.append(Paragraph(interp['summary'], self.styles['Normal']))
                story.append(Spacer(1, 0.3*inch))

            # Production Interpretation
            if 'production_interpretation' in interp:
                prod = interp['production_interpretation']
                story.append(Paragraph("Production Analysis", self.styles['CustomSubtitle']))

                prod_data = [
                    ['Aspect', 'Finding'],
                    ['Production Method', prod.get('method', 'unknown').upper()],
                    ['Confidence', f"{prod.get('confidence', 0):.1%}"],
                    ['Workshop Quality', prod.get('workshop_quality', 'unknown').replace('_', ' ').title()],
                ]

                table = Table(prod_data, colWidths=[2.5*inch, 3.5*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
                ]))
                story.append(table)
                story.append(Spacer(1, 0.15*inch))

                if 'description' in prod:
                    story.append(Paragraph(f"<b>Analysis:</b> {prod['description']}", self.styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))

                if 'evidence' in prod and prod['evidence']:
                    story.append(Paragraph("<b>Supporting Evidence:</b>", self.styles['Normal']))
                    for evidence in prod['evidence']:
                        story.append(Paragraph(f"• {evidence}", self.styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))

                story.append(Spacer(1, 0.3*inch))

            # Use Life Analysis
            if 'use_life' in interp:
                use = interp['use_life']
                story.append(Paragraph("Use-Life Analysis", self.styles['CustomSubtitle']))

                use_data = [
                    ['Aspect', 'Finding'],
                    ['Use Intensity', use.get('intensity', 'unknown').title()],
                    ['Duration', use.get('duration', 'unknown').replace('_', ' ').title()],
                    ['Maintenance Evidence', use.get('maintenance', 'unknown').upper()],
                ]

                table = Table(use_data, colWidths=[2.5*inch, 3.5*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#764ba2')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
                ]))
                story.append(table)
                story.append(Spacer(1, 0.15*inch))

                if 'description' in use:
                    story.append(Paragraph(f"<b>Analysis:</b> {use['description']}", self.styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))

                if 'evidence' in use and use['evidence']:
                    story.append(Paragraph("<b>Supporting Evidence:</b>", self.styles['Normal']))
                    for evidence in use['evidence']:
                        story.append(Paragraph(f"• {evidence}", self.styles['Normal']))

                story.append(Spacer(1, 0.3*inch))

            # Conservation State
            if 'conservation_state' in interp:
                cons = interp['conservation_state']
                story.append(Paragraph("Conservation State", self.styles['CustomSubtitle']))

                cons_data = [
                    ['Aspect', 'Finding'],
                    ['Condition', cons.get('condition', 'unknown').upper()],
                    ['Degradation Type', cons.get('degradation_type', 'unknown').replace('_', ' ').title()],
                    ['Functional', 'YES' if cons.get('functional', False) else 'NO'],
                ]

                table = Table(cons_data, colWidths=[2.5*inch, 3.5*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f687b3')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
                ]))
                story.append(table)
                story.append(Spacer(1, 0.15*inch))

                if 'description' in cons:
                    story.append(Paragraph(f"<b>Analysis:</b> {cons['description']}", self.styles['Normal']))

                story.append(Spacer(1, 0.3*inch))

            # Archaeological Context
            if 'archaeological_context' in interp:
                ctx = interp['archaeological_context']
                story.append(Paragraph("Archaeological Context", self.styles['CustomSubtitle']))

                if 'period_indicators' in ctx and ctx['period_indicators']:
                    story.append(Paragraph("<b>Period Indicators:</b>", self.styles['Normal']))
                    for indicator in ctx['period_indicators']:
                        story.append(Paragraph(f"• {indicator}", self.styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))

                if 'comparative_notes' in ctx:
                    story.append(Paragraph(f"<b>Comparative Analysis:</b> {ctx['comparative_notes']}", self.styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))

                if 'research_value' in ctx:
                    story.append(Paragraph(f"<b>Research Value:</b> {ctx['research_value'].upper()}", self.styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))

                if 'recommendations' in ctx and ctx['recommendations']:
                    story.append(Paragraph("<b>Recommendations:</b>", self.styles['Normal']))
                    for rec in ctx['recommendations']:
                        story.append(Paragraph(f"• {rec}", self.styles['Normal']))

                story.append(Spacer(1, 0.3*inch))

        # === SECTION 3: TECHNICAL DATA ===
        story.append(PageBreak())
        story.append(Paragraph("Technical Analysis Data", self.styles['SectionHeading']))
        story.append(Paragraph(
            "Quantitative measurements and feature detection results.",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 0.2*inch))

        # Production method table
        story.append(Paragraph("Production Method Detection", self.styles['CustomSubtitle']))
        prod_data = [
            ['Feature', 'Value', 'Interpretation'],
            ['Production Method', tech_features.get('production_method', 'N/A'), ''],
            ['Method Confidence', f"{tech_features.get('production_confidence', 0):.1%}", ''],
        ]

        table = Table(prod_data, colWidths=[2.5*inch, 1.5*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
        ]))
        story.append(table)
        story.append(Spacer(1, 0.3*inch))

        # Hammering detection
        story.append(Paragraph("Hammering Analysis", self.styles['CustomSubtitle']))
        hammer_data = [
            ['Feature', 'Value'],
            ['Hammering Detected', 'YES' if tech_features.get('hammering_detected') else 'NO'],
            ['Hammering Intensity', f"{tech_features.get('hammering_intensity', 0):.4f}"],
            ['Threshold', '0.60 (for "forged" classification)'],
        ]

        table = Table(hammer_data, colWidths=[3*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#764ba2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
        ]))
        story.append(table)
        story.append(Spacer(1, 0.3*inch))

        # Casting detection
        story.append(Paragraph("Casting Analysis", self.styles['CustomSubtitle']))
        cast_data = [
            ['Feature', 'Value'],
            ['Likely Cast', 'YES' if tech_features.get('casting_likely') else 'NO'],
            ['Casting Confidence', f"{tech_features.get('casting_confidence', 0):.1%}"],
            ['Surface Smoothness', f"{tech_features.get('surface_smoothness', 0):.4f}"],
        ]

        table = Table(cast_data, colWidths=[3*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f687b3')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
        ]))
        story.append(table)
        story.append(Spacer(1, 0.3*inch))

        # Wear analysis
        story.append(Paragraph("Wear Pattern Analysis", self.styles['CustomSubtitle']))
        wear_data = [
            ['Feature', 'Value'],
            ['Wear Detected', 'YES' if tech_features.get('wear_detected') else 'NO'],
            ['Wear Severity', tech_features.get('wear_severity', 'N/A').upper()],
            ['Edge Rounding', f"{tech_features.get('edge_rounding', 0):.4f}"],
        ]

        table = Table(wear_data, colWidths=[3*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ed8936')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
        ]))
        story.append(table)
        story.append(Spacer(1, 0.3*inch))

        # Edge condition
        story.append(Paragraph("Edge Condition", self.styles['CustomSubtitle']))
        edge_data = [
            ['Feature', 'Value'],
            ['Edge Sharpness', tech_features.get('edge_sharpness', 'N/A').upper()],
            ['Edge Angle', f"{tech_features.get('edge_angle', 0):.2f}°"],
            ['Edge Usable', 'YES' if tech_features.get('edge_usable') else 'NO'],
            ['Thresholds', 'Sharp <30°, Usable <70°'],
        ]

        table = Table(edge_data, colWidths=[3*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#48bb78')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
        ]))
        story.append(table)
        story.append(Spacer(1, 0.3*inch))

        # === SECTION 4: MORPHOMETRIC FEATURES (if available) ===
        if morphometric_features:
            story.append(PageBreak())
            story.append(Paragraph("Morphometric Features", self.styles['SectionHeading']))

            morph_data = [['Feature', 'Value', 'Unit']]
            for key, value in morphometric_features.items():
                if isinstance(value, (int, float)):
                    unit = ''
                    if 'volume' in key.lower():
                        unit = 'mm³'
                    elif 'area' in key.lower():
                        unit = 'mm²'
                    elif key.lower() in ['length', 'width', 'height']:
                        unit = 'mm'
                    morph_data.append([key.replace('_', ' ').title(), f"{value:.2f}", unit])

            table = Table(morph_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
            ]))
            story.append(table)

        # === FOOTER: Technical Details ===
        story.append(PageBreak())
        story.append(Paragraph("Methodology & Technical Details", self.styles['SectionHeading']))

        methodology = f"""
        <b>Analysis Framework:</b> Archaeological Classifier System v1.0<br/>
        <b>3D Rendering:</b> Trimesh + PyRender with archaeological lighting presets<br/>
        <b>Production Analysis:</b> Surface curvature variance, K-D tree spatial analysis<br/>
        <b>Wear Detection:</b> Edge geometry analysis, surface degradation patterns<br/>
        <b>AI Interpretation:</b> Claude Sonnet 4.5 (temperature 0.1, structured JSON output)<br/>
        <b>Thresholds:</b> Hammering >0.60, Sharp edge <30°, Usable edge <70°<br/>
        <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        story.append(Paragraph(methodology, self.styles['Normal']))

        # Build PDF
        doc.build(story, onFirstPage=self._create_header_footer,
                 onLaterPages=self._create_header_footer)

        return pdf_path

    def generate_batch_technological_report(self,
                                            batch_results: Dict,
                                            artifact_meshes: Dict,
                                            ai_batch_interpretation: Optional[Dict] = None) -> str:
        """
        Generate comprehensive batch technological analysis report.

        Args:
            batch_results: Batch analysis results from technological analyzer
            artifact_meshes: Dictionary of {artifact_id: mesh} for 3D rendering
            ai_batch_interpretation: Optional structured AI interpretation for batch

        Returns:
            Path to generated PDF file
        """
        temp_dir = tempfile.gettempdir()
        pdf_filename = f"batch_tech_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(temp_dir, pdf_filename)

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch
        )

        story = []

        # Title
        title = Paragraph(
            "Batch Technological Analysis Report",
            self.styles['CustomTitle']
        )
        story.append(title)

        # Metadata
        metadata = Paragraph(
            f"Archaeological Classifier System<br/>"
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
            f"Total Artifacts: {len(batch_results.get('artifact_results', []))}",
            self.styles['InfoText']
        )
        story.append(metadata)
        story.append(Spacer(1, 0.4*inch))

        # === EXECUTIVE SUMMARY ===
        story.append(Paragraph("Executive Summary", self.styles['SectionHeading']))

        summary = batch_results.get('summary', {})
        summary_data = [
            ['Metric', 'Value'],
            ['Total Artifacts', str(summary.get('total_artifacts', 0))],
            ['Successfully Analyzed', str(summary.get('successful', 0))],
            ['Failed', str(summary.get('failed', 0))],
        ]

        table = Table(summary_data, colWidths=[3*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
        ]))
        story.append(table)
        story.append(Spacer(1, 0.3*inch))

        # === BATCH STATISTICS ===
        stats = batch_results.get('statistics', {})

        # Production methods distribution
        if 'production_methods' in stats:
            story.append(Paragraph("Production Methods Distribution", self.styles['CustomSubtitle']))
            prod_methods = stats['production_methods']

            prod_data = [['Method', 'Count', 'Percentage']]
            for method, count in prod_methods.items():
                total = summary.get('total_artifacts', 1)
                pct = (count / total * 100) if total > 0 else 0
                prod_data.append([method.upper(), str(count), f"{pct:.1f}%"])

            table = Table(prod_data, colWidths=[2*inch, 2*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#764ba2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
            ]))
            story.append(table)
            story.append(Spacer(1, 0.3*inch))

        # Hammering statistics
        if 'hammering' in stats:
            story.append(Paragraph("Hammering Statistics", self.styles['CustomSubtitle']))
            hammer = stats['hammering']

            hammer_data = [
                ['Metric', 'Value'],
                ['Artifacts with Hammering', str(hammer.get('count', 0))],
                ['Average Intensity', f"{hammer.get('avg_intensity', 0):.4f}"],
                ['Maximum Intensity', f"{hammer.get('max_intensity', 0):.4f}"],
            ]

            table = Table(hammer_data, colWidths=[3*inch, 3*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f687b3')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
            ]))
            story.append(table)
            story.append(Spacer(1, 0.3*inch))

        # Wear statistics
        if 'wear' in stats:
            story.append(Paragraph("Wear Statistics", self.styles['CustomSubtitle']))
            wear = stats['wear']

            wear_data = [
                ['Metric', 'Value'],
                ['Artifacts with Wear', str(wear.get('count', 0))],
                ['Heavy Wear', str(wear.get('heavy', 0))],
                ['Average Edge Rounding', f"{wear.get('avg_edge_rounding', 0):.4f}"],
            ]

            table = Table(wear_data, colWidths=[3*inch, 3*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ed8936')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
            ]))
            story.append(table)
            story.append(Spacer(1, 0.3*inch))

        # === AI BATCH INTERPRETATION ===
        if ai_batch_interpretation and 'interpretation' in ai_batch_interpretation:
            story.append(PageBreak())
            story.append(Paragraph("Batch Archaeological Interpretation", self.styles['SectionHeading']))

            interp = ai_batch_interpretation['interpretation']

            if 'collection_overview' in interp:
                story.append(Paragraph("Collection Overview", self.styles['CustomSubtitle']))
                # Handle both string and dict formats
                overview_text = interp['collection_overview']
                if isinstance(overview_text, dict):
                    # Convert dict to readable text
                    overview_text = json.dumps(overview_text, indent=2)
                elif not isinstance(overview_text, str):
                    overview_text = str(overview_text)
                story.append(Paragraph(overview_text, self.styles['Normal']))
                story.append(Spacer(1, 0.3*inch))

            if 'production_patterns' in interp:
                story.append(Paragraph("Production Patterns", self.styles['CustomSubtitle']))
                for key, value in interp['production_patterns'].items():
                    story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {value}", self.styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
                story.append(Spacer(1, 0.2*inch))

            if 'use_patterns' in interp:
                story.append(Paragraph("Use Patterns", self.styles['CustomSubtitle']))
                for key, value in interp['use_patterns'].items():
                    story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {value}", self.styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
                story.append(Spacer(1, 0.2*inch))

            if 'recommendations' in interp and interp['recommendations']:
                story.append(Paragraph("Recommendations", self.styles['CustomSubtitle']))
                for rec in interp['recommendations']:
                    story.append(Paragraph(f"• {rec}", self.styles['Normal']))
                story.append(Spacer(1, 0.3*inch))

        # === INDIVIDUAL ARTIFACTS ===
        story.append(PageBreak())
        story.append(Paragraph("Individual Artifact Analysis", self.styles['SectionHeading']))

        artifact_results = batch_results.get('artifact_results', [])

        for artifact_result in artifact_results:
            artifact_id = artifact_result.get('artifact_id', 'Unknown')
            status = artifact_result.get('status', 'unknown')

            if status != 'success':
                continue

            story.append(Paragraph(f"Artifact: {artifact_id}", self.styles['CustomSubtitle']))

            # 3D Render for this artifact
            if artifact_id in artifact_meshes:
                mesh = artifact_meshes[artifact_id]
                try:
                    render_path = render_artifact_image(mesh, artifact_id, output_dir=temp_dir)
                    if render_path and os.path.exists(render_path):
                        story.append(Image(render_path, width=5*inch, height=3.75*inch))
                        story.append(Spacer(1, 0.2*inch))
                except Exception as e:
                    print(f"Could not render {artifact_id}: {e}")

            # Quick summary table
            features = artifact_result.get('features', {})
            quick_data = [
                ['Feature', 'Value'],
                ['Production Method', features.get('production_method', 'N/A').upper()],
                ['Confidence', f"{features.get('production_confidence', 0):.1%}"],
                ['Hammering', 'YES' if features.get('hammering_detected') else 'NO'],
                ['Hammering Intensity', f"{features.get('hammering_intensity', 0):.4f}"],
                ['Wear Severity', features.get('wear_severity', 'N/A').upper()],
                ['Edge Sharpness', features.get('edge_sharpness', 'N/A').upper()],
                ['Edge Angle', f"{features.get('edge_angle', 0):.2f}°"],
            ]

            table = Table(quick_data, colWidths=[2.5*inch, 3.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
            ]))
            story.append(table)
            story.append(Spacer(1, 0.4*inch))

        # === METHODOLOGY ===
        story.append(PageBreak())
        story.append(Paragraph("Methodology & Technical Details", self.styles['SectionHeading']))

        methodology = f"""
        <b>Analysis Framework:</b> Archaeological Classifier System v1.0<br/>
        <b>Batch Analysis:</b> Parallel processing with statistical aggregation<br/>
        <b>3D Rendering:</b> Trimesh + PyRender with archaeological lighting<br/>
        <b>Production Detection:</b> Surface curvature variance, K-D tree spatial analysis<br/>
        <b>AI Interpretation:</b> Claude Sonnet 4.5 (temperature 0.1, JSON structured)<br/>
        <b>Thresholds:</b> Hammering >0.60, Sharp edge <30°, Usable <70°<br/>
        <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        story.append(Paragraph(methodology, self.styles['Normal']))

        # Build PDF
        doc.build(story, onFirstPage=self._create_header_footer,
                 onLaterPages=self._create_header_footer)

        return pdf_path


def generate_simple_artifact_report(artifact_id, features, mesh):
    """
    Generate a simple single-artifact report.

    Args:
        artifact_id: ID of the artifact
        features: Feature dictionary
        mesh: Trimesh object

    Returns:
        Path to generated PDF
    """
    gen = ReportGenerator()

    temp_dir = tempfile.gettempdir()
    pdf_filename = f"artifact_report_{artifact_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = os.path.join(temp_dir, pdf_filename)

    doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                           rightMargin=inch, leftMargin=inch,
                           topMargin=inch, bottomMargin=inch)

    story = []

    # Title
    title = Paragraph(f"Artifact Report: {artifact_id}", gen.styles['CustomTitle'])
    story.append(title)
    story.append(Spacer(1, 0.5*inch))

    # Features table
    story.append(Paragraph("Morphometric Features", gen.styles['SectionHeading']))

    feature_data = [['Feature', 'Value', 'Unit']]
    for key, value in features.items():
        if isinstance(value, (int, float)):
            feature_data.append([key.replace('_', ' ').title(), f"{value:.2f}", ''])

    table = Table(feature_data, colWidths=[2*inch, 2*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
    ]))

    story.append(table)

    doc.build(story, onFirstPage=gen._create_header_footer,
             onLaterPages=gen._create_header_footer)

    return pdf_path
