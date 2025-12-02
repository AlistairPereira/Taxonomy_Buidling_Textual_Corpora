

# import json
# from pathlib import Path

# import pandas as pd
# import streamlit as st

# # -----------------------------------------------------------------------------
# # Paths & basic config
# # -----------------------------------------------------------------------------
# BASE_DIR = Path(__file__).parent          # prompt_engineering/
# DATA_DIR = BASE_DIR / "data"              # prompt_engineering/data

# st.set_page_config(
#     page_title="Automatic Product Taxonomy Explorer",
#     page_icon="🧭",
#     layout="wide",
# )

# # -----------------------------------------------------------------------------
# # Data loading helpers (cached)
# # -----------------------------------------------------------------------------
# @st.cache_data(show_spinner=False)
# def load_products() -> pd.DataFrame:
#     """
#     Load train + test products into a single df_products table.
#     We keep only columns that are useful for the UI.
#     """
#     dfs = []

#     train_pkl = DATA_DIR / "df_train_taxonomy.pkl"
#     test_pkl = DATA_DIR / "df_test_mapped.pkl"

#     if train_pkl.exists():
#         df_train = pd.read_pickle(train_pkl)
#         df_train["split"] = "train"
#         dfs.append(df_train)

#     if test_pkl.exists():
#         df_test = pd.read_pickle(test_pkl)
#         df_test["split"] = "test"
#         dfs.append(df_test)

#     if not dfs:
#         return pd.DataFrame()

#     df_products = pd.concat(dfs, ignore_index=True)

#     # Ensure expected columns exist to avoid KeyErrors
#     for col in [
#         "Brand",
#         "BrandPartCode",
#         "ProductName",
#         "metadata_text_clean",
#         "A",
#         "B",
#         "C",
#         "path_3",
#         "A_name",
#         "B_name",
#         "C_name",
#         "pred_A_name",
#         "pred_B_name",
#         "pred_C_name",
#     ]:
#         if col not in df_products.columns:
#             df_products[col] = ""

#     return df_products


# @st.cache_data(show_spinner=False)
# def load_hierarchy() -> pd.DataFrame | None:
#     """
#     Load discovered hierarchy (A/B/C + counts).
#     Prefer hierarchy_abc.pkl; fall back to discovered_taxonomy_ABC_clean.csv.
#     """
#     pkl_path = DATA_DIR / "hierarchy_abc.pkl"
#     csv_path = DATA_DIR / "discovered_taxonomy_ABC_clean.csv"

#     if pkl_path.exists():
#         return pd.read_pickle(pkl_path)

#     if csv_path.exists():
#         return pd.read_csv(csv_path)

#     return None


# @st.cache_data(show_spinner=False)
# def load_metrics() -> dict | None:
#     """
#     Load train/test cosine + BERTScore metrics from metrics.json.
#     """
#     metrics_path = DATA_DIR / "metrics.json"
#     if not metrics_path.exists():
#         return None
#     with open(metrics_path, "r", encoding="utf-8") as f:
#         return json.load(f)


# # -----------------------------------------------------------------------------
# # Small utilities
# # -----------------------------------------------------------------------------
# def safe_series(df: pd.DataFrame, col: str) -> pd.Series:
#     """Return a lowercase string Series for a column, or empty strings if missing."""
#     if col not in df.columns:
#         return pd.Series([""] * len(df), index=df.index)
#     return df[col].fillna("").astype(str).str.lower()


# def show_topline_cards(df_products: pd.DataFrame, hierarchy: pd.DataFrame | None):
#     col1, col2, col3, col4 = st.columns(4)

#     with col1:
#         st.metric("Products (loaded)", f"{len(df_products):,}")

#     if hierarchy is not None and not hierarchy.empty:
#         a_count = hierarchy["A_name"].nunique()
#         b_count = hierarchy["B_name"].nunique()
#         c_count = hierarchy["C_name"].nunique()
#     else:
#         a_count = df_products["A_name"].nunique()
#         b_count = df_products["B_name"].nunique()
#         c_count = df_products["C_name"].nunique()

#     with col2:
#         st.metric("A-level categories", a_count if a_count > 0 else "—")
#     with col3:
#         st.metric("B-level categories", b_count if b_count > 0 else "—")
#     with col4:
#         st.metric("C-level categories", c_count if c_count > 0 else "—")


# def bert_to_df(level_dict: dict) -> pd.DataFrame:
#     """Convert level → (P,R,F1) dict to a nice dataframe."""
#     rows = []
#     for lvl, triple in level_dict.items():
#         P, R, F1 = triple
#         rows.append({"Level": lvl, "P": P, "R": R, "F1": F1})
#     return pd.DataFrame(rows).set_index("Level")


# # -----------------------------------------------------------------------------
# # Pages
# # -----------------------------------------------------------------------------
# def page_overview(df_products: pd.DataFrame, hierarchy: pd.DataFrame | None):
#     st.title("Automatic Product Taxonomy – Overview")

#     st.write(
#         """
# This UI lets you explore the **unsupervised taxonomy** that you built from Icecat:

# - Embeddings from **YAKE keywords**
# - **HDBSCAN** clusters for C-level
# - **Agglomerative clustering** for B/A-levels
# - **LLM-generated names** for each node
#         """
#     )

#     st.divider()
#     show_topline_cards(df_products, hierarchy)

#     st.divider()

#     st.subheader("Data & files currently loaded")
#     with st.expander("Details"):
#         st.write("**Data directory:**", f"`{DATA_DIR}`")
#         st.write(
#             "- `df_train_taxonomy.pkl` → train products with discovered A/B/C\n"
#             "- `df_test_mapped.pkl` → test products with gold + predicted taxonomy\n"
#             "- `hierarchy_abc.pkl` / `discovered_taxonomy_ABC_clean.csv` → discovered tree\n"
#             "- `metrics.json` → cosine + BERTScore for train vs test"
#         )


# # ---------- NEW SEARCH IMPLEMENTATION (token-based) ----------
# def page_search_products(df_products: pd.DataFrame):
#     st.title("🔎 Search products & compare taxonomy")

#     if df_products.empty:
#         st.warning("No product data found in `data/`. Please export your train/test tables first.")
#         return

#     st.write(
#         "Type **anything** about a product (brand, model, keywords, or a short phrase). "
#         "We search across brand, part code, product name and descriptions."
#     )

#     query = st.text_input(
#         "Search text",
#         "",
#         placeholder="Examples:  HP 5KM83PA,  HP Omen gaming laptop,  toner cartridge,  1TB SSD …",
#     )

#     if not query.strip():
#         st.info("Enter a search query above to see matching products.")
#         return

#     q = query.lower().strip()

#     # Columns to search
#     s_brand = safe_series(df_products, "Brand")
#     s_code  = safe_series(df_products, "BrandPartCode")
#     s_name  = safe_series(df_products, "ProductName")
#     s_meta  = safe_series(df_products, "metadata_text_clean")

#     # --- token-based search so long queries still work ---
#     import re

#     tokens = [t for t in re.split(r"\W+", q) if len(t) >= 2]

#     if not tokens:
#         # fall back to plain substring
#         mask = (
#             s_brand.str.contains(q, na=False)
#             | s_code.str.contains(q, na=False)
#             | s_name.str.contains(q, na=False)
#             | s_meta.str.contains(q, na=False)
#         )
#     else:
#         # product matches if ANY token appears in ANY field
#         mask = pd.Series(False, index=df_products.index)
#         for t in tokens:
#             t_mask = (
#                 s_brand.str.contains(t, na=False)
#                 | s_code.str.contains(t, na=False)
#                 | s_name.str.contains(t, na=False)
#                 | s_meta.str.contains(t, na=False)
#             )
#             mask |= t_mask

#     results = df_products[mask].copy()

#     st.write(f"**{len(results)}** products matched. Showing first 50:")
#     results = results.head(50)

#     if results.empty:
#         st.info(
#             "No products matched this query in the current subset. "
#             "Try fewer words (e.g., just `hp`, `omen`, or a part code like `5KM83PA`)."
#         )
#         return

#     # Build readable paths
#     def build_gold_path(row):
#         path = row.get("path_3", "")
#         if isinstance(path, str) and path:
#             return path
#         return f"{row.get('A','')} > {row.get('B','')} > {row.get('C','')}"

#     def build_discovered_path(row):
#         a = row.get("A_name", "")
#         b = row.get("B_name", "")
#         c = row.get("C_name", "")
#         if not (a or b or c):
#             return ""
#         return f"{a} > {b} > {c}"

#     def build_predicted_path(row):
#         a = row.get("pred_A_name", "")
#         b = row.get("pred_B_name", "")
#         c = row.get("pred_C_name", "")
#         if not (a or b or c):
#             return ""
#         return f"{a} > {b} > {c}"

#     view = pd.DataFrame(
#         {
#             "split": results["split"],
#             "Brand": results["Brand"],
#             "BrandPartCode": results["BrandPartCode"],
#             "ProductName": results["ProductName"],
#             "Gold taxonomy (Icecat)": [build_gold_path(r) for _, r in results.iterrows()],
#             "Discovered train taxonomy": [build_discovered_path(r) for _, r in results.iterrows()],
#             "Predicted taxonomy (test)": [build_predicted_path(r) for _, r in results.iterrows()],
#         }
#     )

#     st.dataframe(view, width="stretch")


# def page_browse_taxonomy(hierarchy: pd.DataFrame | None):
#     st.title("🌲 Browse discovered taxonomy")

#     if hierarchy is None or hierarchy.empty:
#         st.warning(
#             "No discovered taxonomy file found "
#             "(`discovered_taxonomy_ABC_clean.csv` or `hierarchy_abc.pkl`). "
#             "Export it from your notebook first."
#         )
#         return

#     st.write("This table shows the **A/B/C hierarchy** your model discovered.")
#     st.dataframe(hierarchy, width="stretch")

#     with st.expander("Show as nested text tree"):
#         lines = []
#         for a in sorted(hierarchy["A_name"].dropna().unique()):
#             lines.append(f"A: {a}")
#             subset_a = hierarchy[hierarchy["A_name"] == a]
#             for b in sorted(subset_a["B_name"].dropna().unique()):
#                 lines.append(f"  B: {b}")
#                 subset_b = subset_a[subset_a["B_name"] == b]
#                 for _, row in subset_b.iterrows():
#                     c = row["C_name"]
#                     n = row.get("num_products", None)
#                     if pd.isna(n):
#                         lines.append(f"    C: {c}")
#                     else:
#                         lines.append(f"    C: {c}  ({int(n)} products)")
#             lines.append("")

#         st.code("\n".join(lines), language="text")


# def page_model_metrics(metrics: dict | None):
#     st.title("📊 Model metrics – train vs test")

#     if metrics is None:
#         st.warning("No `metrics.json` found in `data/`. Run your evaluation notebook first.")
#         return

#     train_cos = metrics["train"]["cosine"]
#     test_cos = metrics["test"]["cosine"]

#     st.subheader("Cosine similarity")
#     cos_df = pd.DataFrame(
#         {
#             "Train": train_cos,
#             "Test": test_cos,
#         }
#     )
#     st.table(cos_df)

#     st.divider()
#     st.subheader("BERTScore (P, R, F1)")

#     train_bert = metrics["train"]["bertscore"]
#     test_bert = metrics["test"]["bertscore"]

#     col3, col4 = st.columns(2)
#     with col3:
#         st.caption("Train")
#         bdf = bert_to_df(train_bert)
#         st.table(bdf[["P", "R", "F1"]])

#     with col4:
#         st.caption("Test")
#         bdf = bert_to_df(test_bert)
#         st.table(bdf[["P", "R", "F1"]])


# # -----------------------------------------------------------------------------
# # Main app
# # -----------------------------------------------------------------------------
# def main():
#     df_products = load_products()
#     hierarchy = load_hierarchy()
#     metrics = load_metrics()

#     with st.sidebar:
#         st.title("📂 Taxonomy Explorer")
#         st.write("Go to:")
#         page = st.radio(
#             "",
#             ["Overview", "Search products", "Browse taxonomy", "Model metrics"],
#             index=0,
#         )
#         st.markdown("---")
#         st.markdown(
#             """
# Tip:
# - Use **Search products** to verify a few items.
# - Use **Browse taxonomy** to inspect the tree.
# - Use **Model metrics** for thesis screenshots.
#             """
#         )

#     if page == "Overview":
#         page_overview(df_products, hierarchy)
#     elif page == "Search products":
#         page_search_products(df_products)
#     elif page == "Browse taxonomy":
#         page_browse_taxonomy(hierarchy)
#     elif page == "Model metrics":
#         page_model_metrics(metrics)


# if __name__ == "__main__":
#     main()


import json
from pathlib import Path

import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# Paths & basic config
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent          # prompt_engineering/
DATA_DIR = BASE_DIR / "data"              # prompt_engineering/data

st.set_page_config(
    page_title="Automatic Product Taxonomy Explorer",
    page_icon="🧭",
    layout="wide",
)

# -----------------------------------------------------------------------------
# Data loading helpers (cached)
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_products() -> pd.DataFrame:
    """
    Load train + test products into a single df_products table.
    We keep only columns that are useful for the UI.
    """
    dfs = []

    train_pkl = DATA_DIR / "df_train_taxonomy.pkl"
    test_pkl = DATA_DIR / "df_test_mapped.pkl"

    if train_pkl.exists():
        df_train = pd.read_pickle(train_pkl)
        df_train["split"] = "train"
        dfs.append(df_train)

    if test_pkl.exists():
        df_test = pd.read_pickle(test_pkl)
        df_test["split"] = "test"
        dfs.append(df_test)

    if not dfs:
        return pd.DataFrame()

    df_products = pd.concat(dfs, ignore_index=True)

    # Ensure expected columns exist to avoid KeyErrors
    for col in [
        "Brand",
        "BrandPartCode",
        "ProductName",
        "metadata_text_clean",
        "A",
        "B",
        "C",
        "path_3",
        "A_name",
        "B_name",
        "C_name",
        "pred_A_name",
        "pred_B_name",
        "pred_C_name",
    ]:
        if col not in df_products.columns:
            df_products[col] = ""

    return df_products


@st.cache_data(show_spinner=False)
def load_hierarchy() -> pd.DataFrame | None:
    """
    Load discovered hierarchy (A/B/C + counts).
    Prefer hierarchy_abc.pkl; fall back to discovered_taxonomy_ABC_clean.csv.
    """
    pkl_path = DATA_DIR / "hierarchy_abc.pkl"
    csv_path = DATA_DIR / "discovered_taxonomy_ABC_clean.csv"

    if pkl_path.exists():
        return pd.read_pickle(pkl_path)

    if csv_path.exists():
        return pd.read_csv(csv_path)

    return None


# -----------------------------------------------------------------------------
# Small utilities
# -----------------------------------------------------------------------------
def safe_series(df: pd.DataFrame, col: str) -> pd.Series:
    """Return a lowercase string Series for a column, or empty strings if missing."""
    if col not in df.columns:
        return pd.Series([""] * len(df), index=df.index)
    return df[col].fillna("").astype(str).str.lower()


def show_topline_cards(df_products: pd.DataFrame, hierarchy: pd.DataFrame | None):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Products (loaded)", f"{len(df_products):,}")

    if hierarchy is not None and not hierarchy.empty:
        a_count = hierarchy["A_name"].nunique()
        b_count = hierarchy["B_name"].nunique()
        c_count = hierarchy["C_name"].nunique()
    else:
        a_count = df_products["A_name"].nunique()
        b_count = df_products["B_name"].nunique()
        c_count = df_products["C_name"].nunique()

    with col2:
        st.metric("A-level categories", a_count if a_count > 0 else "—")
    with col3:
        st.metric("B-level categories", b_count if b_count > 0 else "—")
    with col4:
        st.metric("C-level categories", c_count if c_count > 0 else "—")


# -----------------------------------------------------------------------------
# Pages
# -----------------------------------------------------------------------------
def page_overview(df_products: pd.DataFrame, hierarchy: pd.DataFrame | None):
    st.title("Automatic Product Taxonomy – Overview")

    st.write(
        """
This UI lets you explore the **unsupervised taxonomy** that you built from Icecat:

- Embeddings from **YAKE keywords**
- **HDBSCAN** clusters for C-level
- **Agglomerative clustering** for B/A-levels
- **LLM-generated names** for each node
        """
    )

    st.divider()
    show_topline_cards(df_products, hierarchy)

    st.divider()

    st.subheader("Data & files currently loaded")
    with st.expander("Details"):
        st.write("**Data directory:**", f"`{DATA_DIR}`")
        st.write(
            "- `df_train_taxonomy.pkl` → train products with discovered A/B/C\n"
            "- `df_test_mapped.pkl` → test products with gold + predicted taxonomy\n"
            "- `hierarchy_abc.pkl` / `discovered_taxonomy_ABC_clean.csv` → discovered tree\n"
        )


# ---------- SEARCH PAGE ----------
# def page_search_products(df_products: pd.DataFrame):
#     st.title("🔎 Search products & compare taxonomy")

#     if df_products.empty:
#         st.warning("No product data found in `data/`. Please export your train/test tables first.")
#         return

#     st.write(
#         "Type **anything** about a product (brand, model, keywords, or a short phrase). "
#         "We search across brand, part code, product name and descriptions."
#     )

#     query = st.text_input(
#         "Search text",
#         "",
#         placeholder="Examples:  HP 5KM83PA,  HP Omen gaming laptop,  toner cartridge,  1TB SSD …",
#     )

#     if not query.strip():
#         st.info("Enter a search query above to see matching products.")
#         return

#     q = query.lower().strip()

#     # Columns to search
#     s_brand = safe_series(df_products, "Brand")
#     s_code  = safe_series(df_products, "BrandPartCode")
#     s_name  = safe_series(df_products, "ProductName")
#     s_meta  = safe_series(df_products, "metadata_text_clean")

#     # --- token-based search so long queries still work ---
#     import re

#     tokens = [t for t in re.split(r"\W+", q) if len(t) >= 2]

#     if not tokens:
#         # fall back to plain substring
#         mask = (
#             s_brand.str.contains(q, na=False)
#             | s_code.str.contains(q, na=False)
#             | s_name.str.contains(q, na=False)
#             | s_meta.str.contains(q, na=False)
#         )
#     else:
#         # product matches if ANY token appears in ANY field
#         mask = pd.Series(False, index=df_products.index)
#         for t in tokens:
#             t_mask = (
#                 s_brand.str.contains(t, na=False)
#                 | s_code.str.contains(t, na=False)
#                 | s_name.str.contains(t, na=False)
#                 | s_meta.str.contains(t, na=False)
#             )
#             mask |= t_mask

#     results = df_products[mask].copy()

#     st.write(f"**{len(results)}** products matched. Showing first 50:")
#     results = results.head(50)

#     if results.empty:
#         st.info(
#             "No products matched this query in the current subset. "
#             "Try fewer words (e.g., just `hp`, `omen`, or a part code like `5KM83PA`)."
#         )
#         return

#     # Build readable paths
#     def build_gold_path(row):
#         path = row.get("path_3", "")
#         if isinstance(path, str) and path:
#             return path
#         return f"{row.get('A','')} > {row.get('B','')} > {row.get('C','')}"

#     def build_discovered_path(row):
#         a = row.get("A_name", "")
#         b = row.get("B_name", "")
#         c = row.get("C_name", "")
#         if not (a or b or c):
#             return ""
#         return f"{a} > {b} > {c}"

#     def clean_label(x):
#         """Treat NaN and 'nan' as empty."""
#         if pd.isna(x):
#             return ""
#         if isinstance(x, str) and x.strip().lower() in {"", "nan", "none"}:
#             return ""
#         return x.strip() if isinstance(x, str) else str(x)

#     def build_predicted_path(row):
#         # Only show predictions for TEST rows
#         if row.get("split", "") != "test":
#             return ""

#         a = clean_label(row.get("pred_A_name", ""))
#         b = clean_label(row.get("pred_B_name", ""))
#         c = clean_label(row.get("pred_C_name", ""))

#         if not (a or b or c):
#             return ""

#         return f"{a} > {b} > {c}"

#     view = pd.DataFrame(
#         {
#             "split": results["split"],
#             "Brand": results["Brand"],
#             "BrandPartCode": results["BrandPartCode"],
#             "ProductName": results["ProductName"],
#             "Gold taxonomy (Icecat)": [build_gold_path(r) for _, r in results.iterrows()],
#             "Discovered train taxonomy": [build_discovered_path(r) for _, r in results.iterrows()],
#             "Predicted taxonomy (test)": [build_predicted_path(r) for _, r in results.iterrows()],
#         }
#     )

#     st.dataframe(view, width="stretch")

def page_search_products(df_products: pd.DataFrame):
    st.title("🔎 Search products & compare taxonomy")

    if df_products.empty:
        st.warning("No product data found in `data/`. Please export your train/test tables first.")
        return

    st.write(
        "Type **anything** about a product (brand, model, keywords, or a short phrase). "
        "We will show you the taxonomy it falls into."
    )

    query = st.text_input(
        "Search text",
        "",
        placeholder="Examples:  HP Omen gaming laptop,  Samsung SSD 1TB,  toner cartridge …",
    )

    if not query.strip():
        st.info("Enter a search query above to see matching products.")
        return

    q = query.lower().strip()

    # Columns to search
    s_brand = safe_series(df_products, "Brand")
    s_code  = safe_series(df_products, "BrandPartCode")
    s_name  = safe_series(df_products, "ProductName")
    s_meta  = safe_series(df_products, "metadata_text_clean")

    # --- token-based search so long queries still work ---
    import re
    tokens = [t for t in re.split(r"\W+", q) if len(t) >= 2]

    if not tokens:
        mask = (
            s_brand.str.contains(q, na=False)
            | s_code.str.contains(q, na=False)
            | s_name.str.contains(q, na=False)
            | s_meta.str.contains(q, na=False)
        )
    else:
        mask = pd.Series(False, index=df_products.index)
        for t in tokens:
            t_mask = (
                s_brand.str.contains(t, na=False)
                | s_code.str.contains(t, na=False)
                | s_name.str.contains(t, na=False)
                | s_meta.str.contains(t, na=False)
            )
            mask |= t_mask

    results = df_products[mask].copy()

    st.write(f"**{len(results)}** products matched. Showing first 50:")
    results = results.head(50)

    if results.empty:
        st.info(
            "No products matched this query in the current subset. "
            "Try fewer words (e.g., just `hp`, `omen`, or a part code like `5KM83PA`)."
        )
        return

    # ---- Build a single final taxonomy per row ----
    def clean_label(x):
        if pd.isna(x):
            return ""
        if isinstance(x, str) and x.strip().lower() in {"", "nan", "none"}:
            return ""
        return x.strip() if isinstance(x, str) else str(x)

    def pick_taxonomy(row):
        # 1) Prefer predicted taxonomy for TEST rows
        if row.get("split", "") == "test":
            a = clean_label(row.get("pred_A_name", ""))
            b = clean_label(row.get("pred_B_name", ""))
            c = clean_label(row.get("pred_C_name", ""))
            if a or b or c:
                return " > ".join([x for x in [a, b, c] if x])

        # 2) Else use discovered A/B/C names (train taxonomy)
        a = clean_label(row.get("A_name", ""))
        b = clean_label(row.get("B_name", ""))
        c = clean_label(row.get("C_name", ""))
        if a or b or c:
            return " > ".join([x for x in [a, b, c] if x])

        # 3) Else fall back to original Icecat path_3
        path3 = row.get("path_3", "")
        if isinstance(path3, str) and path3.strip():
            return path3.strip()

        return ""

    final_taxonomies = [pick_taxonomy(r) for _, r in results.iterrows()]

    # What the user sees: product + ONE taxonomy column
    view = pd.DataFrame(
        {
            "BrandPartCode": results["BrandPartCode"],
            "ProductName": results["ProductName"],
            "Taxonomy": final_taxonomies,
        }
    )

    st.dataframe(view, width="stretch")



def page_browse_taxonomy(hierarchy: pd.DataFrame | None):
    st.title("🌲 Browse discovered taxonomy")

    if hierarchy is None or hierarchy.empty:
        st.warning(
            "No discovered taxonomy file found "
            "(`discovered_taxonomy_ABC_clean.csv` or `hierarchy_abc.pkl`). "
            "Export it from your notebook first."
        )
        return

    st.write("This table shows the **A/B/C hierarchy** your model discovered.")
    st.dataframe(hierarchy, width="stretch")

    with st.expander("Show as nested text tree"):
        lines = []
        for a in sorted(hierarchy["A_name"].dropna().unique()):
            lines.append(f"A: {a}")
            subset_a = hierarchy[hierarchy["A_name"] == a]
            for b in sorted(subset_a["B_name"].dropna().unique()):
                lines.append(f"  B: {b}")
                subset_b = subset_a[subset_a["B_name"] == b]
                for _, row in subset_b.iterrows():
                    c = row["C_name"]
                    n = row.get("num_products", None)
                    if pd.isna(n):
                        lines.append(f"    C: {c}")
                    else:
                        lines.append(f"    C: {c}  ({int(n)} products)")
            lines.append("")

        st.code("\n".join(lines), language="text")


# -----------------------------------------------------------------------------
# Main app
# -----------------------------------------------------------------------------
def main():
    df_products = load_products()
    hierarchy = load_hierarchy()

    with st.sidebar:
        st.title("📂 Taxonomy Explorer")
        st.write("Go to:")
        page = st.radio(
            "",
            ["Overview", "Search products", "Browse taxonomy"],
            index=0,
        )
        st.markdown("---")
        st.markdown(
            """
Tip:
- Use **Search products** to verify a few items.
- Use **Browse taxonomy** to inspect the tree.
            """
        )

    if page == "Overview":
        page_overview(df_products, hierarchy)
    elif page == "Search products":
        page_search_products(df_products)
    elif page == "Browse taxonomy":
        page_browse_taxonomy(hierarchy)


if __name__ == "__main__":
    main()

print("--------------------------------above one without model metrics---------------------------------")