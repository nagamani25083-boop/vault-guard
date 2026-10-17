# Design and Output Template
## Brief
Title, theme, audience, player count, estimated duration, difficulty, venue/web, objective, supplied assets, and stated assumptions. Learning objectives are conditional.
## Player edition
Opening story, explicit goal, interaction rules, available clues, answer format, hints and exit options. Exclude host solutions.
## Host edition: one record per puzzle
- Unique ID / title / prerequisites / all-or-any prerequisite policy
- Complete clue text and reveal timing; actual location or complete text of necessary assets
- Input type / exact format / canonical answer / accepted aliases / normalization
- Stepwise derivation and grounds for excluding other answers
- Three hint levels / reveal explanation / reward / successors
- Estimated time / accessibility (never encode solely through color)
## Dependencies and Hosting
Draw a text dependency graph and check for cycles. Starting puzzles have no prerequisites; define completion explicitly. For physical games, add materials, setup, offline backup, free exit, and hosting instructions. Include debrief questions. Create printable files only when requested.
## Self-contained miniature (a validation example, not mandatory game content)
P1 states: “Enter the digits on cards one, two, three, in that order.” Card three=2, card one=4, card two=7. Answer string: 472.
P2 appears only after P1 succeeds. Its card states: “A=1,B=2,C=3; convert CAB to three digits.” Answer: 312. Its reward explicitly states: “The finale digit is 6.”
P3 appears only after P2 succeeds: “Concatenate the last digit of the first answer with the finale digit.” Answer: 26.
Graph: P1→P2→P3. P3 uses 2 from completed P1 and 6 from an earned reward, never a future clue. Hints direct attention to ordering, lookup, and concatenation without introducing hidden rules.
