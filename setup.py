import setuptools

if __name__ == "__main__":
    setuptools.setup(
        use_scm_version={"local_scheme": "no-local-version"},
        setup_requires=["setuptools_scm[toml]>=3.5.0"],
    )
