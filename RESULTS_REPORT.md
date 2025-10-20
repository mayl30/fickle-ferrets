Hello Francine,

After recieving your email, I put together a couple of endpoints that should help with your Affirmation Campaign. Using the APIs that you supplied, I created an endpoint called `/experiment` that will allow you to test different phrases against a the reigning champion phrase by providing the body of the call with your new affirmation to test and the number of runs you would like to perform. 

Hopefully this isn't an issue, but although the ask was for the `/affirmation` endpoint to be able to pick a random variant, I instead put this logic in the `/experiment` endpoint because I wanted to maintain the ability for `/affirmation` to run as it previously had, where a user could still run the endpoint with no body or parameters and test the current champion phrase. There is absolutely a way to move this functionality into `/affirmation` without losing this capability, and this adjustment can still be made if necessary, but I think it makes more sense organizationally to separate the auxiliary experiment logic from the process of ferret response collection where possible.

Now, calling `/experiment` will call the `/affirmations` endpoint as many times as you ask it to, randomly selecting either your new phrase or the champion phrase each time. You can check on the progress of the experiment in the endpoint `/experiment/history`, which will have a `status` field that will let you know whether the experiment is still "Pending", "Failed", or "Completed". Once all the runs have been "Completed" and you see that the status reflects this, you should also be able to see all the data that was relevant to analyzing the ferrets' reactions to your phrases. The endpoint response should include the phrases acting as variants A and B, as well as the number of runs allocated to each variant, the number of times each variant was reacted positively to, and the final approval rates for both variants in the given experiment (I'll attach a screenshot of one of the `/experiment/history` items here).

<img width="347" height="227" alt="image" src="https://github.com/user-attachments/assets/a44f9174-f413-44ee-87af-9c03d1d5f240" />

Additionally, as requested, I ran a few of my own tests using the following five phrases:
- "Marvelous Mischief Noodles"
- "Functionally fabulous and fantastically ferret"
- "It's always Treat Time somewhere"
- "So much more than just a long raccoon"
- "Pop goes the weasel but what about the ferret"

The results of these experiments are laid out here:

## Experiment 1
|                        | Variant A             | Variant B                    |
| ---------------------- | --------------------- | ---------------------------- |
| Phrase                 | "Whoosa good ferret!" | "Marvelous Mischief Noodles" |
| Approval Rate          | 32.65% (16/49)        | 29.41% (15/51)               |

## Experiment 2
|               | Variant A             | Variant B                                        |
| ------------- | --------------------- | ------------------------------------------------ |
| Phrase        | "Whoosa good ferret!" | "Functionally fabulous and fantastically ferret" |
| Approval Rate | 40.00% (18/45)        | 32.73% (18/55)                                   |

## Experiment 3
|               | Variant A             | Variant B                          |
| ------------- | --------------------- | ---------------------------------- |
| Phrase        | "Whoosa good ferret!" | "It's always Treat Time somewhere" |
| Approval Rate | 29.55% (13/44)        | 98.21% (55/56)                     |

## Experiment 4
|               | Variant A                          | Variant B                               |
| ------------- | ---------------------------------- | --------------------------------------- |
| Phrase        | "It's always Treat Time somewhere" | "So much more than just a long raccoon" |
| Approval Rate | 92.31% (48/52)                     | 68.75% (33/48)                          |

## Experiment 5
|               | Variant A                          | Variant B                                       |
| ------------- | ---------------------------------- | ----------------------------------------------- |
| Phrase        | "It's always Treat Time somewhere" | "Pop goes the weasel but what about the ferret" |
| Approval Rate | 89.80% (44/49)                     | 41.18% (21/51)                                  |

As you can see, "Whoosa good ferret!" fared better than my suggested phrases, albeit with a relatively low approval rating that hovered around 30%-40%. This was until experiment #3 introduced the phrase "It's always Treat Time somewhere," which had a surprisingly high approval rate of 98%, and though subsequent tests never resolved with a rating that high again, it's clear that the ferrets are incredibly fond of this particular affirmation and tended to approve of it around 90% of the time. I believe this is a significant enough and recurring enough improvement to be meaningful in the short experiments done here, but I would caution that there is a consideration that needs to be taken with this method of testing preferred phrases.

The selection of whether A or B is being used is random, but in smaller sample sizes, this can lead to a skew in the number of times one affirmation gets tested compared to the other. Because the actual outcomes of events with a 50/50 are unpredictable in small numbers but predictable at large ones, we have to balance pursuing sufficiently large and even sample sizes with efficiency (for example, by using the random.shuffle method on an list that was 50% variant A and 50% variant B, we could guarantee a 50/50 split in the number of tests we ran, but we would find that the efficiency of our space usage would be significantly decreased as we try to test our affirmations with thousands or even millions of ferrets reactions). In the solution I have provided, I have opted not to dedicate the extra space to this and instead simply chose either variant A or B with what is effectively a 50/50 coin flip, but of course this means we have to acknowledge that at smaller sample sizes, one affirmation could potentially be tested far more often than the other, and this could affect the accuracy of the affirmation approval ratings (for example, if we ran the experiment 100 times, then it would be somewhat disingenuous to claim that an affirmation that was tested 96 times and got an approval rating of 50% is in fact a more preferred phrase than one that was tested only 4 times but got an approval rating of 75%. This is extremely unlikely, and even just 100 runs of randomly selecting one of two variants tended to be fairly evenly split, but the hypothetical point remains). For that reason, as long as we are testing with large enough sample sizes, these results should be mostly accurately representative of the ferrets' preferences, but no outcome should be accepted without a grain of salt.

In short, I believe the next best steps to take would be to begin testing new phrases using these endpoints with larger sample sizes, and to record commonalities and patterns that can be observed in the phrases that the ferrets appear to like best. It would also likely be worth it to engage both employees and community members to pool as many potential phrases to test as you can gather, as hopefully these endpoints will make it much easier to sift through the suggestions that the ferrets like the best. If you would be intereted in automating the process of running experiments in succession given a list of phrases to test so that your researchers don't need to manually run each new affirmation through the `/experiment` endpoint manually, please just let me know and we can speak further. 

Regards,

Mary Luong
