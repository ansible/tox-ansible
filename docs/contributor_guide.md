# Contributor Guide

To contribute to `tox-ansible`, please use pull requests on a branch of your own fork.

After [creating your fork on GitHub], you can do:

```shell-session
$ git clone --recursive git@github.com:your-name/tox-ansible
$ cd tox-ansible
$ git checkout -b your-branch-name
# DO SOME CODING HERE
$ git add your new files
$ git commit -v
$ git push origin your-branch-name
```

You will then be able to create a pull request from your commit.

Prerequisites:

1. All fixes to core functionality (i.e. anything except docs or examples) should
   be accompanied by tests that fail prior to your change and succeed afterwards.

2. Before sending a PR, make sure that `tox -e lint` passes.

Feel free to raise issues in the repo if you feel unable to contribute a code
fix.

Possible security bugs should be reported via email to <mailto:security@ansible.com>.

## Talk to us

### Code of Conduct

Please read and adhere to the [Ansible Community Code of Conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html) in all your interactions within the Ansible community.

### Forum

Join the [Ansible Forum](https://forum.ansible.com) as a single starting point and our default communication platform for questions and help, development discussions, events, and much more. [Register](https://forum.ansible.com/signup?) to join the community. Search by categories and tags to find interesting topics or start a new one; subscribe only to topics you need!

- [Get Help](https://forum.ansible.com/c/help/6): get help or help others. Please add appropriate tags if you start new discussions, for example `devtools`.
- [Posts tagged with 'devtools'](https://forum.ansible.com/tag/devtools): subscribe to participate in project-related conversations.
- [Bullhorn newsletter](https://docs.ansible.com/ansible/devel/community/communication.html#the-bullhorn) used to announce releases and important changes.
- [Social Spaces](https://forum.ansible.com/c/chat/4): gather and interact with fellow enthusiasts.
- [News & Announcements](https://forum.ansible.com/c/news/5): track project-wide announcements including social events.

See `Navigating the Ansible forum <https://forum.ansible.com/t/navigating-the-ansible-forum-tags-categories-and-concepts/39>`_ for some practical advice on finding your way around.

### Matrix

For real-time interactions, conversations in the community happen over the Matrix protocol in the [#devtools:ansible.com](https://matrix.to/#/#devtools:ansible.com).

For more information, see the community-hosted [Matrix FAQ](https://hackmd.io/@ansible-community/community-matrix-faq).

[creating your fork on github]: https://docs.github.com/en/get-started/quickstart/contributing-to-projects
